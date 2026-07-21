import assert from "node:assert/strict";
import test from "node:test";

import {
  GENERAL_NO_BIRTH_TIME_REFUSAL,
  guardGeneralNoBirthTimeOutput,
  guardPreciseTimingOutput,
} from "../src/lib/timing-output-guard.ts";
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

test("general mode structurally rejects personalized chart placements in Chinese and English", () => {
  const unsafeClaims = [
    "你的七宫落入摩羯。",
    "盘面显示你的事业宫很强。",
    "你的金星落第七宫。",
    "你的上升落在巨蟹座。",
    "你的 D9 显示婚姻会晚一些。",
    "Your Venus is in the 7th house.",
    "Your ascendant falls in Cancer.",
    "Your D9 chart shows a strong marriage house.",
  ];

  for (const claim of unsafeClaims) {
    const guarded = guardGeneralNoBirthTimeOutput(claim);
    assert.equal(guarded.includes(GENERAL_NO_BIRTH_TIME_REFUSAL), true, claim);
    assert.equal(guarded.includes(claim.replace(/[。.]$/, "")), false, claim);
  }

  assert.equal(
    guardGeneralNoBirthTimeOutput("第七宫在占星概念中常与关系相关。"),
    "第七宫在占星概念中常与关系相关。",
  );
  assert.equal(
    guardGeneralNoBirthTimeOutput("Venus is generally associated with relating and values."),
    "Venus is generally associated with relating and values.",
  );
  assert.equal(
    guardGeneralNoBirthTimeOutput("你问的第七宫，在占星概念中常与关系相关。"),
    "你问的第七宫，在占星概念中常与关系相关。",
  );
});

test("hidden AYANAM comments cannot split a personalized claim around the guard", async () => {
  const title = "<!--AYANAM_TITLE:一般占星咨询-->";
  const suggestions = '<!--AYANAM_SUGGESTIONS:["了解第七宫的一般概念","先完成生时校正","改问一般知识"]-->';
  async function* reply() {
    yield "一般知识可以说明概念。你的<!";
    yield "--AYANAM_TITLE:一般占星咨询--";
    yield ">金星落";
    yield "第七宫。\n<!--AYANAM_SUGGEST";
    yield 'IONS:["了解第七宫的一般概念","先完成生时校正","改问一般知识"]-->';
  }

  const response = streamTextResponse(reply(), {
    mode: "mastra",
    requestId: "00000000-0000-4000-8000-000000000097",
    transformText: createBirthTimeModeOutputGuard("general_no_birth_time", false),
  });
  const text = await response.text();
  const parsed = parseAgentReply(text, "general");

  assert.match(text, /一般知识可以说明概念/);
  assert.match(text, new RegExp(GENERAL_NO_BIRTH_TIME_REFUSAL));
  assert.doesNotMatch(text, /你的\s*金星落第七宫/);
  assert.equal(text.includes(title), true);
  assert.equal(text.includes(suggestions), true);
  assert.equal(parsed.title, "一般占星咨询");
  assert.deepEqual(parsed.suggestions, ["了解第七宫的一般概念", "先完成生时校正", "改问一般知识"]);
});
