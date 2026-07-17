import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const projectFile = (path: string) => new URL(`../${path}`, import.meta.url);
const readProjectFile = (path: string) => readFileSync(projectFile(path), "utf8");

test("provides the generic composable sidebar primitive", () => {
  assert.equal(existsSync(projectFile("src/components/ui/sidebar.tsx")), true);
});

test("exports only the retained sidebar composition surface", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  for (const name of [
    "SidebarProvider", "Sidebar", "SidebarHeader", "SidebarContent",
    "SidebarGroup", "SidebarGroupLabel", "SidebarGroupContent",
    "SidebarMenu", "SidebarMenuItem", "SidebarMenuButton",
    "SidebarFooter", "SidebarInset", "SidebarTrigger", "SidebarRail", "useSidebar",
  ]) {
    assert.match(sidebar, new RegExp(`export (?:function|const) ${name}\\b`));
  }
  assert.doesNotMatch(sidebar, /SidebarMenuBadge|SidebarMenuSkeleton|SidebarMenuSub|side\?:|variant\?:/);
});

test("keeps sidebar behavior in the generic primitive", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  assert.match(sidebar, /useSidebarViewport/);
  assert.match(sidebar, /defaultSidebarOpen/);
  assert.match(sidebar, /shouldHandleSidebarShortcut/);
  assert.match(sidebar, /data-state/);
  assert.match(sidebar, /data-viewport/);
  assert.match(sidebar, /data-mobile-open/);
  assert.match(sidebar, /addEventListener\("keydown"/);
  assert.match(sidebar, /preventDefault\(\)/);
  assert.match(sidebar, /const label = expanded \? "Close sidebar" : "Open sidebar"/);
  assert.match(sidebar, /viewport === "mobile"\) return;[\s\S]*setOpenMobile\(false\)/);
  assert.match(sidebar, /@base-ui\/react\/tooltip/);
  assert.doesNotMatch(sidebar, /Sheet/);
  assert.match(sidebar, /cn\(/);
  assert.doesNotMatch(sidebar, /#[0-9a-fA-F]{3,8}|hsl\(/);
});

test("documents the sidebar shell design contract", () => {
  const design = readProjectFile("DESIGN.md");
  assert.match(design, /### Sidebar shell/);
  assert.match(design, /Scroll ownership/);
  assert.match(design, /session-local/);
});
