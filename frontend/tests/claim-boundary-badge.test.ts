import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const rowSource = readFileSync(new URL("../src/components/chat-message-row.tsx", import.meta.url), "utf8");
const badgeSource = readFileSync(new URL("../src/components/claim-boundary-badge.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

test("assistant messages do not expose the internal claim boundary badge", () => {
  assert.doesNotMatch(rowSource, /ClaimBoundaryBadge/);
  assert.doesNotMatch(rowSource, /status=\{message\.techniqueTruth\}/);
  assert.match(badgeSource, /不把未闭环内容包装成确定预测/);
  assert.match(badgeSource, /observation_only/);
  assert.match(badgeSource, /reference_only/);
  assert.match(globalStyles, /\.claim-boundary-badge/);
});
