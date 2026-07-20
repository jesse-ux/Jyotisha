import assert from "node:assert/strict";
import test from "node:test";

import { guardPreciseTimingOutput } from "../src/lib/timing-output-guard.ts";
import { streamTextResponse } from "../src/lib/stream-text-response.ts";
import { parseAgentReply } from "../src/lib/agent-reply.ts";
import { createBirthTimeModeOutputGuard } from "../src/lib/consultation-birth-time-mode.ts";

test("removes exact dates and months when precise timing is blocked", () => {
  const guarded = guardPreciseTimingOutput(
    "你会在2027年3月15日结婚，事业将在11月转折。",
  );

  assert.doesNotMatch(guarded, /2027年3月15日|11月/);
  assert.match(guarded, /具体时间已省略/);
});

test("removes guarantee conclusions when the evidence contract is incomplete", () => {
  const guarded = guardPreciseTimingOutput("我保证你一定会升职。");

  assert.doesNotMatch(guarded, /保证你一定会升职/);
  assert.match(guarded, /保证性结论已省略/);
  assert.equal(
    guardPreciseTimingOutput("You will definitely get promoted."),
    "[保证性结论已省略].",
  );
});

test("guards a date that crosses streamed chunks", async () => {
  async function* reply() {
    yield "应期是2027年";
    yield "3月15日，但我保证你一定会升职。";
  }

  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000098",
    transformText: guardPreciseTimingOutput,
  });
  const text = await response.text();

  assert.doesNotMatch(text, /2027年3月15日|保证你一定会升职/);
  assert.match(text, /保证性结论已省略/);
});

test("guards only visible prose and preserves AYANAM blocks across arbitrary chunk boundaries", async () => {
  const suggestions = '<!--AYANAM_SUGGESTIONS:["你一定会升职吗？","D9 是什么？","先完成生时校正"]-->';
  const title = "<!--AYANAM_TITLE:一般占星咨询-->";
  const longVisiblePrefix = "一般知识不依赖个人星盘。".repeat(100);
  async function* reply() {
    yield `${longVisiblePrefix}正文说你将在2027年`;
    yield "3月15日一定会升职。\n<!";
    yield "--AYANAM_SUGGESTIONS:[\"你一定会升职吗？\",\"D9 是什么？\",\"先完成生时校正\"]--";
    yield ">\n<!--AYANAM_TIT";
    yield "LE:一般占星咨询-->";
  }

  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000099",
    transformText: createBirthTimeModeOutputGuard("general_no_birth_time", false),
  });
  const text = await response.text();
  const parsed = parseAgentReply(text, "general");

  assert.doesNotMatch(text, /2027年3月15日|正文说你将在.*一定会升职/);
  assert.match(text, /^一般知识不依赖个人星盘/);
  assert.match(text, /具体时间已省略|保证性结论已省略/);
  assert.equal(text.includes(suggestions), true);
  assert.equal(text.includes(title), true);
  assert.doesNotMatch(text, /<!\[/);
  assert.deepEqual(parsed.suggestions, ["你一定会升职吗？", "D9 是什么？", "先完成生时校正"]);
  assert.equal(parsed.title, "一般占星咨询");
});
