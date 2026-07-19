import assert from "node:assert/strict";
import test from "node:test";

import { guardPreciseTimingOutput } from "../src/lib/timing-output-guard.ts";
import { streamTextResponse } from "../src/lib/stream-text-response.ts";

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
    transformText: guardPreciseTimingOutput,
  });
  const text = await response.text();

  assert.doesNotMatch(text, /2027年3月15日|保证你一定会升职/);
  assert.match(text, /保证性结论已省略/);
});
