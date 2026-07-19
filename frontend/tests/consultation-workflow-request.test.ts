import assert from "node:assert/strict";
import test from "node:test";
import { projectConsultationWorkflowRequest } from "../src/lib/consultation-workflow-request.ts";
import { runConsultationWorkflow } from "../src/mastra/index.ts";
import type { ConsultationInput } from "../src/mastra/index.ts";

test("timing questions use a legal report theme and preserve a timing route hint", () => {
  // Given: a public timing consultation question.
  const question = "未来哪些阶段值得把握？";

  // When: its workflow request is projected for the Python service.
  const request = projectConsultationWorkflowRequest(question, "timing");

  // Then: the illegal public theme is converted to a legal report theme with a route hint.
  assert.deepEqual(request, {
    question: "应期与阶段问题：未来哪些阶段值得把握？",
    themes: ["career"],
  });
});

test("timing input projects only legal private workflow fields", async () => {
  // Given: a public timing input and a Python workflow response.
  const input: ConsultationInput = {
    year: 1990,
    month: 1,
    day: 1,
    hour: 12,
    minute: 0,
    lat: 25,
    lon: 121,
    tz: 8,
    city: "台北",
    question: "未来哪些阶段值得把握？",
    theme: "timing",
    entryMode: "direct_chart",
  };
  let requestBody = "";
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (_input, init) => {
    requestBody = typeof init?.body === "string" ? init.body : "";
    return new Response(JSON.stringify({
      success: true,
      chart: {},
      routing: {},
      consumer_context: {
        route: "career",
        core_status: "ready",
        available_layers: [],
        missing_route_layers: [],
        hard_blockers: [],
        answer_policy: {
          can_answer_direction: true,
          can_answer_precise_timing: false,
        },
      },
    }), { status: 200 });
  };

  try {
    // When: the adapter invokes the Python workflow.
    await runConsultationWorkflow(input);
  } finally {
    globalThis.fetch = originalFetch;
  }

  // Then: private workflow fields are projected without mutating public input.
  const body = JSON.parse(requestBody);
  assert.equal(body.question, "应期与阶段问题：未来哪些阶段值得把握？");
  assert.equal(body.question_text, "应期与阶段问题：未来哪些阶段值得把握？");
  assert.deepEqual(body.theme, ["career"]);
  assert.doesNotMatch(requestBody, /"timing"/);
  assert.equal(input.question, "未来哪些阶段值得把握？");
  assert.equal(input.theme, "timing");
});
