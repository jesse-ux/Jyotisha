import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { chatMessageViews } from "../src/lib/chat-message-view.ts";

const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
const messageRowSource = readFileSync(new URL("../src/components/chat-message-row.tsx", import.meta.url), "utf8");
const activitySource = readFileSync(new URL("../src/components/agent-activity-status.tsx", import.meta.url), "utf8");

const previousMessages = [
  { role: "user", text: "问题" },
] as const;

test("keeps the assistant render identity stable when streaming settles", () => {
  // Given: one assistant answer exists first as a transient stream.
  const streaming = chatMessageViews(previousMessages, true, "完整答案");

  // When: the same answer becomes part of the persisted transcript.
  const settled = chatMessageViews([
    ...previousMessages,
    { role: "assistant", text: "完整答案" },
  ], false, "");

  // Then: React receives the same key and can reuse the existing message shell.
  assert.equal(streaming.at(-1)?.renderKey, settled.at(-1)?.renderKey);
  assert.equal(streaming.at(-1)?.state, "streaming");
  assert.equal(settled.at(-1)?.state, "settled");
});

test("does not duplicate a completed assistant answer while loading state settles", () => {
  // Given: the final answer has entered the transcript while request cleanup lags.
  const completedMessages = [
    ...previousMessages,
    { role: "assistant", text: "完整答案" },
  ] as const;

  // When: the render view is derived with the old loading flag still true.
  const views = chatMessageViews(completedMessages, true, "完整答案");

  // Then: only the persisted answer is rendered.
  assert.equal(views.length, completedMessages.length);
  assert.equal(views.at(-1)?.state, "settled");
});

test("shows honest agent activity states before and during streamed text", () => {
  assert.match(messageRowSource, /message\.state === "thinking"[\s\S]*?\? "working"/);
  assert.match(messageRowSource, /message\.state === "thinking" \? "正在核对星盘信息…"/);
  assert.match(messageRowSource, /message\.state !== "settled"/);
  assert.match(messageRowSource, /message\.state === "thinking" \? "working" : "composing"/);
  assert.match(messageRowSource, /message\.text && <ChatMessageContent text=\{message\.text\}/);
  assert.match(activitySource, /<ThinkingOrb aria-hidden="true" state=\{state\} size=\{20\}/);
  assert.doesNotMatch(activitySource, /CircleCheck|回答已完成|completed/);
  assert.doesNotMatch(messageRowSource, /: "completed"/);
  assert.doesNotMatch(globalStyles, /\.thinking\b/);
});

test("keeps the suggestion row height stable while an answer streams", () => {
  // Given: a completed answer already supplies follow-up suggestions.
  const suggestionBlock = pageSource.match(/\{activeSuggestions\.length > 0[\s\S]*?<div className="composer-suggestions"[\s\S]*?<\/div>\n\s*\)\}/);

  // When: the suggestion visibility and button state are inspected.
  assert.ok(suggestionBlock);

  // Then: loading disables the actions without removing their layout slot.
  assert.doesNotMatch(suggestionBlock[0].split("<div className=", 1)[0], /!isLoading/);
  assert.match(suggestionBlock[0], /disabled=\{[^}]*isLoading/);
});

test("docks the composer inside the chat panel instead of floating over content", () => {
  assert.match(pageSource, /<div className=\{`composer-wrap \$\{starterHomeVisible \? "composer-wrap-starter" : ""\}`\}>/);
  assert.match(globalStyles, /\.chat-panel[^}]*grid-template-rows:\s*68px minmax\(0,\s*1fr\) auto/);
  assert.match(globalStyles, /\.conversation[^}]*padding-bottom:\s*var\(--composer-reserve\)/);
  assert.match(globalStyles, /\.composer-wrap[^}]*position:\s*sticky/);
  assert.match(globalStyles, /\.composer-wrap[^}]*bottom:\s*0/);
  assert.doesNotMatch(globalStyles, /\.composer-wrap[^}]*position:\s*fixed/);
});
