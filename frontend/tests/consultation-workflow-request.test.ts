import assert from "node:assert/strict";
import test from "node:test";
import { projectConsultationWorkflowRequest } from "../src/lib/consultation-workflow-request.ts";

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
