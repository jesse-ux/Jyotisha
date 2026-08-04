import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  defaultGuidedJyotishTopics,
  generalGuidedJyotishTopics,
} from "../src/lib/guided-jyotish-topics.ts";

const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
const globalStyles = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
const appSidebarSource = readFileSync(new URL("../src/components/app-sidebar.tsx", import.meta.url), "utf8");
const guidedTopicsSource = readFileSync(new URL("../src/lib/guided-jyotish-topics.ts", import.meta.url), "utf8");

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

test("completed account initialization switches directly to the home cards", () => {
  assert.doesNotMatch(pageSource, /setOnboardingJustCompleted\(true\)/);
  assert.doesNotMatch(pageSource, /!profileComplete \|\| onboardingJustCompleted/);
});

test("default starter questions are guided Jyotish topics with evidence and claim boundaries", () => {
  assert.match(pageSource, /defaultGuidedJyotishTopics/);
  assert.match(pageSource, /starterSuggestions\.map/);
  assert.match(pageSource, /starterThemes\.find\(\(candidate\) => candidate\.id === item\.theme\)/);
  assert.match(pageSource, /chooseSuggestedQuestion\(item\.text, item\.theme\)/);
  assert.match(guidedTopicsSource, /strictWorkflowRoute/);
  assert.match(guidedTopicsSource, /evidencePreview/);
  assert.match(guidedTopicsSource, /confidenceCap/);
  assert.match(guidedTopicsSource, /claimBoundary/);
  assert.match(guidedTopicsSource, /D10/);
  assert.match(guidedTopicsSource, /D9/);
  assert.match(guidedTopicsSource, /Ashtakavarga/);
  assert.match(guidedTopicsSource, /独立 holdout/);
});

test("profiles without a usable birth minute only receive general-knowledge homepage prompts", () => {
  assert.deepEqual(generalGuidedJyotishTopics.map((topic) => topic.id), defaultGuidedJyotishTopics.map((topic) => topic.id));
  assert.deepEqual(generalGuidedJyotishTopics.map((topic) => topic.prompt), [
    "印度占星一般会从哪些因素理解事业方向？",
    "印度占星一般如何分析关系模式？",
    "印度占星一般如何分析财富结构与风险？",
    "印度占星中的时间推运通常会看哪些因素？",
  ]);
  assert.match(pageSource, /const starterThemes = personalChartAvailable \? themes : generalGuidedJyotishTopics/);
  assert.match(pageSource, /personalChartAvailable[\s\S]*?回答一般占星知识/);
  assert.match(pageSource, /完成生时校正后，再讨论个人星盘结论/);
  assert.match(pageSource, /personalChartAvailable \? "daily_starlanguage" : null/);
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
  // Given: the page-owned selection callback and the app sidebar session action.
  const selectSession = pageSource.match(/function selectSession\(sessionId: string\) \{([\s\S]*?)\n  \}/);

  // When: request-time navigation constraints are inspected.
  // Then: pending request state cannot disable read-only session switching.
  assert.ok(selectSession);
  assert.doesNotMatch(selectSession[1], /pendingSessionId|isLoading|cancellationPending|creatingSession/);
  assert.match(appSidebarSource, /onSelectSession\(session\.id\)/);
  assert.doesNotMatch(appSidebarSource, /pendingSession|isLoading|cancellationPending|requestPending/);
});

test("sizes the model popup to its content with responsive bounds", () => {
  // Given: the model selector popup styles.
  const popupStyles = sourceBetween(globalStyles, ".model-selector-popup {", "}\n.model-selector-popup[data-starting-style]");

  // When: its responsive width is inspected.
  // Then: short labels stay compact while long content remains viewport-safe.
  assert.match(popupStyles, /width:\s*max-content/);
  assert.match(popupStyles, /min-width:\s*180px/);
  assert.match(popupStyles, /max-width:\s*min\(420px,/);
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

test("routes account actions through a menu and focused dialogs", () => {
  // Given: the account surface state and entry-point handlers.
  // When: the page source is inspected for independent menu and dialog routes.
  // Then: each account task has a focused destination instead of one combined sheet.
  assert.match(pageSource, /const \[accountMenuOpen, setAccountMenuOpen\] = useState\(false\)/);
  assert.match(pageSource, /const \[activeAccountDialog, setActiveAccountDialog\] = useState<AccountDialog \| null>\(null\)/);
  assert.match(pageSource, /openAccountDialog\("profile"/);
  assert.match(pageSource, /openAccountDialog\("redeem"/);
  assert.match(pageSource, /openAccountDialog\("logout"/);
  assert.match(appSidebarSource, /<Menu\.Popup className="account-menu-popup"/);
  assert.doesNotMatch(appSidebarSource, /<Menu\.Popup className="account-menu"/);
  assert.match(appSidebarSource, /<Menu\.Root open=\{accountMenuOpen\} onOpenChange=\{onAccountMenuOpenChange\} modal=\{false\}>/);
});

test("removes the monolithic account sheet", () => {
  // Given: the former sheet implementation names.
  // When: the page and global styles are inspected.
  // Then: no right-side account sheet remains.
  assert.doesNotMatch(pageSource, /profile-overlay|profile-dialog|openAccount\(/);
  assert.doesNotMatch(globalStyles, /\.profile-overlay|\.profile-dialog/);
});

test("keeps admin navigation separate from account task dialogs", () => {
  // Given: the administrator-only route and the new account menu.
  // When: their source relationship is inspected.
  // Then: code management stays a guarded navigation action rather than a modal.
  assert.match(appSidebarSource, /account\.isAdmin\s*&&\s*<Menu\.LinkItem[^>]+render=\{<Link href="\/admin\/codes" \/>\}/);
});

test("keeps the empty starter home at the top instead of auto-scrolling", () => {
  const autoScrollEffect = sourceBetween(
    pageSource,
    "useEffect(() => {\n    if (starterHomeVisible) return;",
    "profileComplete, starterHomeVisible]);",
  );

  assert.match(autoScrollEffect, /if \(starterHomeVisible\) return/);
  assert.match(autoScrollEffect, /conversationEnd\.current\?\.scrollIntoView/);
});

test("does not submit the composer while an IME composition is active", () => {
  const keyHandler = sourceBetween(
    pageSource,
    "function handleComposerKeyDown",
    "\n\n  if (!hydrated",
  );

  assert.match(keyHandler, /if \(event\.nativeEvent\.isComposing\) return/);
  assert.match(keyHandler, /event\.currentTarget\.form\?\.requestSubmit\(\)/);
});

test("announces conversation errors to assistive technology", () => {
  assert.match(pageSource, /<p className="error-message" role="alert">\{activeError\}<\/p>/);
});
