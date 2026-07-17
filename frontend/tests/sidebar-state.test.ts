import assert from "node:assert/strict";
import test from "node:test";
import {
  defaultSidebarOpen,
  shouldHandleSidebarShortcut,
  sidebarViewportForWidth,
} from "../src/lib/sidebar-state.ts";

test("classifies the exact sidebar breakpoints", () => {
  assert.equal(sidebarViewportForWidth(0), "mobile");
  assert.equal(sidebarViewportForWidth(767), "mobile");
  assert.equal(sidebarViewportForWidth(768), "tablet");
  assert.equal(sidebarViewportForWidth(1023), "tablet");
  assert.equal(sidebarViewportForWidth(1024), "desktop");
});

test("uses the approved reload defaults", () => {
  assert.equal(defaultSidebarOpen("mobile"), false);
  assert.equal(defaultSidebarOpen("tablet"), false);
  assert.equal(defaultSidebarOpen("desktop"), true);
});

test("accepts Command or Control B only outside editable controls", () => {
  const shortcut = { key: "b", metaKey: true, ctrlKey: false, altKey: false, shiftKey: false };

  assert.equal(shouldHandleSidebarShortcut({ ...shortcut, target: null }), true);
  assert.equal(shouldHandleSidebarShortcut({ ...shortcut, target: { tagName: "TEXTAREA" } }), false);
  assert.equal(shouldHandleSidebarShortcut({ ...shortcut, target: { isContentEditable: true } }), false);
  assert.equal(shouldHandleSidebarShortcut({ ...shortcut, key: "k", target: null }), false);
});
