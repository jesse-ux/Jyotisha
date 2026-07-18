import assert from "node:assert/strict";
import test from "node:test";
import { protectOnboardingPhrases } from "../src/lib/onboarding-copy.ts";

test("onboarding copy protects short Chinese semantic phrases from line breaks", () => {
  const protectedCopy = protectOnboardingPhrases(
    "不确定也没关系，不会要求你猜一个具体时间；约 14:30（前后 30 分钟）。当前证据用于关键经历，但不代表真实出生分钟，原始填报时间仍会保留。以及，你出生在哪里？",
  );

  for (const phrase of [
    "不\u2060确\u2060定",
    "具\u2060体\u2060时\u2060间",
    "前\u2060后\u2060\u00a0\u20603\u20600\u2060\u00a0\u2060分\u2060钟",
    "当\u2060前\u2060证\u2060据",
    "关\u2060键\u2060经\u2060历",
    "真\u2060实\u2060出\u2060生\u2060分\u2060钟",
    "原\u2060始\u2060填\u2060报\u2060时\u2060间",
    "以\u2060及",
    "你\u2060出\u2060生\u2060在\u2060哪\u2060里",
  ]) {
    assert.ok(protectedCopy.includes(phrase), `missing protected phrase: ${phrase}`);
  }
});

test("onboarding copy protects complete guided-question phrases longest first", () => {
  const phrases = [
    "一个具体时间",
    "关系进入",
    "关系结束",
    "关系明显转变",
    "学习方向变化",
    "学习环境变化",
    "当前排盘使用时间",
    "原始填报时间",
    "候选代表时间",
    "升学、转学或学习方向变化",
    "关系结束或关系明显转变",
    "带日期的关键经历",
    "可以调整",
  ];
  const protectedCopy = protectOnboardingPhrases(phrases.join("，"));

  for (const phrase of phrases) {
    const joined = Array.from(phrase).join("\u2060");
    assert.ok(protectedCopy.includes(joined), `missing complete protected phrase: ${phrase}`);
  }
  assert.equal(
    protectOnboardingPhrases("一个具体时间"),
    "一\u2060个\u2060具\u2060体\u2060时\u2060间",
  );
});
