import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { birthTimeUserError } from "../src/lib/birth-time-user-error.ts";

test("birth-time errors never expose browser implementation messages", () => {
  assert.equal(
    birthTimeUserError(new DOMException("The string did not match the expected pattern.")),
    "候选时间暂时无法保存，请检查网络后重试。",
  );
});

test("birth-time errors preserve a safe server message", () => {
  assert.equal(birthTimeUserError(new Error("候选结果已变化")), "候选结果已变化");
});

test("all guided journey mutations normalize implementation errors", () => {
  const source = readFileSync(new URL("../src/hooks/use-birth-time-guided-journey.ts", import.meta.url), "utf8");
  assert.ok((source.match(/setError\(birthTimeUserError\(caught\)\)/g) ?? []).length >= 1);
  assert.equal(source.includes("setError(caught.message"), false);
  const automatic = readFileSync(new URL("../src/hooks/use-birth-time-automatic-journey-effects.ts", import.meta.url), "utf8");
  assert.equal((automatic.match(/setError\(birthTimeUserError\(caught\)\)/g) ?? []).length, 2);
});
