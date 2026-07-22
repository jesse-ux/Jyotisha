import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const readProjectFile = (path: string) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const globalStyles = readProjectFile("src/app/globals.css");
const messageRowSource = readProjectFile("src/components/chat-message-row.tsx");

test("aligns the session transcript and composer to one readable column", () => {
  assert.match(globalStyles, /--session-column-width:\s*760px/);
  assert.match(globalStyles, /\.conversation:not\(\.is-empty\):not\(\.is-rectification\) \.message-list\s*\{[^}]*width:\s*min\(calc\(var\(--session-column-width\)/);
  assert.match(globalStyles, /\.conversation:not\(\.is-empty\):not\(\.is-rectification\) \+ \.composer-wrap \.composer[^\{]*\{[^}]*width:\s*min\(var\(--session-column-width\),\s*100%\)/);
  assert.match(globalStyles, /\.conversation:not\(\.is-empty\):not\(\.is-rectification\) \+ \.composer-wrap \.composer-suggestions[^\{]*[\s\S]*?width:\s*min\(var\(--session-column-width\),\s*100%\)/);
});

test("keeps message motion restrained and honors reduced-motion preferences", () => {
  assert.match(messageRowSource, /gsap\.matchMedia\(\)/);
  assert.match(messageRowSource, /prefers-reduced-motion:\s*no-preference/);
  assert.match(messageRowSource, /duration:\s*message\.role === "user" \? 0\.3 : 0\.42/);
  assert.match(messageRowSource, /clearProps:\s*"opacity,transform,visibility"/);
});

test("lets model controls fit their labels and keeps the stop action on-brand", () => {
  assert.match(globalStyles, /\.model-selector-trigger\s*\{[^}]*width:\s*fit-content/);
  assert.match(globalStyles, /\.model-selector-popup\s*\{[^}]*width:\s*max-content[^}]*min-width:\s*180px[^}]*max-width:\s*min\(420px,/);
  assert.match(globalStyles, /\.model-selector-copy b\s*\{[^}]*overflow:\s*visible[^}]*white-space:\s*normal/);
  assert.doesNotMatch(globalStyles, /\.model-selector-copy b\s*\{[^}]*text-overflow:\s*ellipsis/);
  assert.match(globalStyles, /\.composer \.composer-stop\s*\{[^}]*background:\s*var\(--color-action\)/);
  assert.match(globalStyles, /\.composer \.composer-stop:not\(:disabled\):hover\s*\{[^}]*background:\s*var\(--color-action-hover\)/);
});
