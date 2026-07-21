import assert from "node:assert/strict";
import test from "node:test";
import { parseAgentReply, resolveSessionTitle } from "../src/lib/agent-reply.ts";

test("extracts a model-generated session title without exposing hidden metadata", () => {
  // Given
  const response = [
    "你目前更适合先验证新的职业方向。",
    '<!--AYANAM_SUGGESTIONS:["什么时候行动？","适合什么方向？","有哪些风险？"]-->',
    "<!--AYANAM_TITLE:未来半年职业转型-->",
  ].join("\n");

  // When
  const reply = parseAgentReply(response, "career");

  // Then
  assert.equal(reply.text, "你目前更适合先验证新的职业方向。");
  assert.equal(reply.title, "未来半年职业转型");
});

test("rejects an overlong model-generated session title", () => {
  // Given
  const response = "回答正文\n<!--AYANAM_TITLE:这是一个明显超过合理长度并且不适合作为会话标题的模型输出标题-->";

  // When
  const reply = parseAgentReply(response, "general");

  // Then
  assert.equal(reply.text, "回答正文");
  assert.equal(reply.title, undefined);
});

test("accepts a concise English model-generated session title", () => {
  // Given
  const response = "Your next step is to test the market first.\n<!--AYANAM_TITLE:Career Change Timing-->";

  // When
  const reply = parseAgentReply(response, "career");

  // Then
  assert.equal(reply.title, "Career Change Timing");
});

test("hides an incomplete metadata block while a reply is streaming", () => {
  // Given
  const response = "回答正文\n<!--AYANAM_TITLE:未来半年";

  // When
  const reply = parseAgentReply(response, "general");

  // Then
  assert.equal(reply.text, "回答正文");
});

test("general no-birth-time replies keep a question-specific session title", () => {
  assert.equal(resolveSessionTitle("工作变化的重点是什么？", "一般占星咨询"), "工作变化的重点是什么");
  assert.equal(resolveSessionTitle("如何理解印度占星里的行星关系？"), "如何理解印度占星里的行星关系");
  assert.equal(resolveSessionTitle("工作变化的重点是什么？", "事业方向与工作变化"), "事业方向与工作变化");
});
