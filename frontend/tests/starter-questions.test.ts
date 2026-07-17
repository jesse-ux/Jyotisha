import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

function sourceBetween(source: string, startMarker: string, endMarker: string) {
  const start = source.indexOf(startMarker);
  const end = source.indexOf(endMarker, start);
  assert.notEqual(start, -1);
  assert.notEqual(end, -1);
  return source.slice(start, end);
}

test("keeps starter questions visible while the user edits a draft", () => {
  // Given: the empty-session starter block and its render guard.
  const guardStart = pageSource.indexOf("{profileComplete && presetMessageFinished");
  const onboardingBranch = pageSource.indexOf("(onboardingPending ?", guardStart);

  // When: the guard is inspected independently of the card copy and layout.
  assert.notEqual(guardStart, -1);
  assert.notEqual(onboardingBranch, -1);
  const starterVisibilityGuard = pageSource.slice(guardStart, onboardingBranch);

  // Then: draft text cannot hide the cards before a message is submitted.
  assert.doesNotMatch(starterVisibilityGuard, /\bdraft\b/);
});

test("keeps follow-up suggestions visible while the user edits a draft", () => {
  // Given: the follow-up suggestion block and its render guard.
  const suggestionGuard = sourceBetween(
    pageSource,
    "{activeSuggestions.length > 0",
    "(\n            <div className=\"composer-suggestions\"",
  );

  // When: the visibility inputs are inspected before the suggestion markup.
  // Then: only submission-related request state may hide the current set.
  assert.doesNotMatch(suggestionGuard, /\bdraft\b/);
});

test("keeps session history clickable while another session is answering", () => {
  // Given: the existing-session navigation block.
  const sessionNavigation = sourceBetween(
    pageSource,
    '<div className="session-list">',
    "</div>\n        </nav>",
  );

  // When: request-time navigation constraints are inspected.
  // Then: pending request state cannot disable read-only session switching.
  assert.doesNotMatch(sessionNavigation, /disabled=\{/);
});

test("uses the compact model popup width", () => {
  // Given: the model selector popup styles.
  const popupStyles = sourceBetween(globalStyles, ".model-selector-popup {", "}\n.model-selector-popup[data-starting-style]");

  // When: its responsive width is inspected.
  // Then: the desktop cap is half of the former 360px width.
  assert.match(popupStyles, /width:\s*min\(180px,/);
});

test("centers the credit value with its icon", () => {
  // Given: the credit value styles next to the existing flex-centered icon.
  const creditValueStyles = sourceBetween(globalStyles, ".credit-button span {", "}\n.credit-button .credit-icon");

  // When: the value line box is inspected.
  // Then: it participates in flex centering without extra line-height drift.
  assert.match(creditValueStyles, /display:\s*inline-flex/);
  assert.match(creditValueStyles, /align-items:\s*center/);
  assert.match(creditValueStyles, /line-height:\s*1/);
});
