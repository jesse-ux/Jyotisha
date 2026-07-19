import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  consultationEntrypointSchema,
  resolveConsultationQuestion,
} from "../src/lib/consultation-entrypoint.ts";

test("plain consultation questions remain user-authored", () => {
  // Given: an ordinary question without a product entrypoint.
  const visibleQuestion = "未来半年适合换工作吗？";

  // When: the server resolves the model-facing question.
  const resolved = resolveConsultationQuestion({
    visibleQuestion,
    entrypoint: undefined,
    currentDate: "2026-07-19",
  });

  // Then: the server does not rewrite ordinary user input.
  assert.deepEqual(resolved, { kind: "plain", modelQuestion: visibleQuestion });
});

test("daily entrypoint selects a private server expansion", () => {
  // Given: the public short label and its closed entrypoint identity.
  const visibleQuestion = "深入看今日";

  // When: the server resolves the request.
  const resolved = resolveConsultationQuestion({
    visibleQuestion,
    entrypoint: "daily_starlanguage",
    currentDate: "2026-07-19",
  });

  // Then: routing is explicit and the model receives more than the public label.
  assert.equal(resolved.kind, "expanded");
  assert.notEqual(resolved.modelQuestion, visibleQuestion);
});

test("birth-time entrypoint selects a private server expansion", () => {
  // Given: a completed profile starts another rectification from a public label.
  const visibleQuestion = "再次校正";

  // When: the server resolves the request.
  const resolved = resolveConsultationQuestion({
    visibleQuestion,
    entrypoint: "birth_time_rectification",
    currentDate: "2026-07-19",
  });

  // Then: the model question is expanded without changing the visible transcript.
  assert.equal(resolved.kind, "expanded");
  assert.notEqual(resolved.modelQuestion, visibleQuestion);
});

test("consultation entrypoints form a closed public request enum", () => {
  assert.equal(consultationEntrypointSchema.safeParse("daily_starlanguage").success, true);
  assert.equal(consultationEntrypointSchema.safeParse("birth_time_rectification").success, true);
  assert.equal(consultationEntrypointSchema.safeParse("client_prompt").success, false);
});

test("browser source does not own private entrypoint prompts", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.doesNotMatch(source, /function buildDailyStarlanguageQuestion/);
  assert.doesNotMatch(source, /function buildBirthTimeRectificationQuestion/);
  assert.doesNotMatch(source, /请结合已校验的星盘资料/);
  assert.doesNotMatch(source, /请基于已校验的出生资料继续/);
});

test("composer keeps the public question and clears hidden routing after edits", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(source, /chooseSuggestedQuestion\("深入看今日",\s*"timing",\s*"daily_starlanguage"\)/s);
  assert.match(source, /birthTimeDisplay \? "再次校正" : "生时校正",\s*"timing",\s*"birth_time_rectification"/s);
  assert.match(source, /messages:\s*\[\.\.\.preservedMessages,\s*\{ role: "user", text: question \}\]/s);
  assert.match(source, /body:\s*JSON\.stringify\(\{[\s\S]*?entrypoint:\s*entrypoint \?\? undefined,[\s\S]*?question,/);
  assert.match(source, /onChange=\{\(event\) => \{\s*setDraft\(event\.target\.value\);\s*setDraftTheme\(null\);\s*setDraftEntrypoint\(null\);/s);
  assert.match(source, /setDraft\(pending\.question\);\s*setDraftTheme\(pending\.theme\);\s*setDraftEntrypoint\(pending\.entrypoint\);/s);
});

test("consult route expands an optional entrypoint for both Agent and tool input", () => {
  const source = readFileSync(new URL("../src/app/api/consult/route.ts", import.meta.url), "utf8");

  assert.match(source, /entrypoint:\s*consultationEntrypointSchema\.optional\(\)/);
  assert.match(source, /question:\s*resolvedQuestion\.modelQuestion/);
  assert.match(source, /resolvedQuestion\.modelQuestion,\s*"\\n需要查询星盘时/s);
});

test("homepage entrypoints use two whole-card native actions", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const wholeCardActions = source.match(/className="product-entrypoint-hitarea"/g) ?? [];

  assert.equal(wholeCardActions.length, 2);
  assert.doesNotMatch(source, /className="daily-starlanguage-heading">[\s\S]{0,180}<button/);
});
