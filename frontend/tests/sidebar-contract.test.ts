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
  assert.match(sidebar, /viewport === "mobile" \|\| !openMobile\) return;[\s\S]*setOpenMobile\(false\)/);
  assert.match(sidebar, /@base-ui\/react\/tooltip/);
  assert.doesNotMatch(sidebar, /Sheet/);
  assert.match(sidebar, /cn\(/);
  assert.doesNotMatch(sidebar, /#[0-9a-fA-F]{3,8}|hsl\(/);
});

test("provides the mobile drawer closing surface", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  assert.match(sidebar, /data-sidebar="scrim"/);
  assert.match(sidebar, /data-slot="sidebar-scrim"/);
  assert.match(sidebar, /aria-label="关闭聊天记录"/);
  assert.match(sidebar, /onClick=\{\(\) => setOpenMobile\(false\)\}/);
  assert.match(sidebar, /isMobile && openMobile \? <button/);
});

test("keeps the sidebar subtree stable while toggling its mobile scrim", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  assert.match(sidebar, /return <>\s*\{sidebar\}\s*\{isMobile && openMobile \? <button/);
});

test("cancels a stale mobile drawer focus frame", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  assert.match(sidebar, /const focusDrawer = window\.requestAnimationFrame/);
  assert.match(sidebar, /return \(\) => window\.cancelAnimationFrame\(focusDrawer\);/);
});

test("uses the approved localized trigger actions", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  assert.match(sidebar, /"收起侧边栏"/);
  assert.match(sidebar, /"展开侧边栏"/);
  assert.match(sidebar, /"打开聊天记录"/);
  assert.match(sidebar, /"关闭聊天记录"/);
});

test("keeps provider primitive defaults and consumer handlers composable", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  assert.match(sidebar, /id=\{id \?\? "chat-sidebar"\}/);
  assert.match(sidebar, /if \(viewport === "mobile" \|\| !openMobile\) return;/);
  assert.match(sidebar, /onClick\?\.\(event\);\s*if \(!event\.defaultPrevented\) setOpen\(!open\);/);
});

test("retains viewport state within an unchanged breakpoint", () => {
  const viewportHook = readProjectFile("src/hooks/use-sidebar-viewport.ts");
  assert.match(viewportHook, /previous\.ready && previous\.viewport === viewport \? previous : \{ viewport, ready: true \}/);
});

test("documents the sidebar shell design contract", () => {
  const design = readProjectFile("DESIGN.md");
  assert.match(design, /### Sidebar shell/);
  assert.match(design, /Scroll ownership/);
  assert.match(design, /session-local/);
});

test("composes the Jyotisha app sidebar from the generic shell", () => {
  assert.equal(existsSync(projectFile("src/components/app-sidebar.tsx")), true);
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");

  for (const component of ["SidebarHeader", "SidebarContent", "SidebarFooter", "SidebarRail"]) {
    assert.match(appSidebar, new RegExp(`<${component}\\b`));
  }
});

test("renders the mobile drawer close trigger in the app sidebar brand row", () => {
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");

  assert.match(appSidebar, /<div className="brand-row">[\s\S]*<SidebarTrigger placement="sidebar" \/>[\s\S]*<\/div>/);
});

test("uses one collapsed history action instead of icon-only session rows", () => {
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");
  assert.match(appSidebar, /MessageSquareText/);
  assert.match(appSidebar, /state === "collapsed" && !isMobile/);
  assert.match(appSidebar, /sessions\.map/);
  assert.doesNotMatch(appSidebar, /sessions\.map\([^)]*\)\s*=>\s*<[^>]+aria-label=/);
});

test("keeps session navigation independent of request state", () => {
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");
  assert.match(appSidebar, /onSelectSession\(session\.id\)/);
  assert.doesNotMatch(appSidebar, /pendingSession|isLoading|cancellationPending|requestPending/);
});

test("uses a portaled Base UI account popover with safe collision padding", () => {
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");
  assert.match(appSidebar, /import \{ Popover \} from "@base-ui\/react\/popover"/);
  assert.match(appSidebar, /<Popover\.Portal>/);
  assert.match(appSidebar, /collisionPadding=\{12\}/);
  assert.match(appSidebar, /<Popover\.Popup className="account-menu-popup"/);
  assert.doesNotMatch(appSidebar, /<Popover\.Popup className="account-menu"/);
});

test("closes an open account menu when the sidebar viewport or state changes", () => {
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");
  assert.match(appSidebar, /const \{[^}]*\bviewport\b[^}]*\} = useSidebar\(\)/);
  assert.match(appSidebar, /const popoverPlacement = `\$\{viewport\}:\$\{state\}`/);
  assert.match(appSidebar, /previousPopoverPlacement/);
  assert.match(appSidebar, /previousPopoverPlacement\.current !== popoverPlacement && accountMenuOpen/);
});

test("keeps app sidebar props as product data and callbacks", () => {
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");
  assert.match(appSidebar, /export type AppSidebarProps/);
  assert.match(appSidebar, /onSelectSession: \(sessionId: string\) => void/);
  assert.doesNotMatch(appSidebar, /supabase|fetch\(|\/api\//i);
});

test("composes the chat page with the app sidebar shell", () => {
  const page = readProjectFile("src/app/page.tsx");

  assert.match(page, /<SidebarProvider escapeBlocked=\{accountMenuOpen \|\| activeAccountDialog !== null\}>/);
  assert.match(page, /<main className="chat-app">[\s\S]*<AppSidebar\b/);
  assert.match(page, /<SidebarInset className="chat-panel" inert=\{activeAccountDialog !== null\}>/);
  assert.match(page, /<SidebarTrigger placement="inset" \/>/);
});

test("removes page-local mobile sidebar ownership", () => {
  const page = readProjectFile("src/app/page.tsx");

  assert.doesNotMatch(page, /mobileSidebarOpen|setMobileSidebarOpen/);
  assert.doesNotMatch(page, /className="sidebar-backdrop"/);
  assert.doesNotMatch(page, /<aside className="sidebar"/);
  assert.doesNotMatch(page, /className="mobile-menu"/);
});

test("blocks the provider mobile Escape action behind layered account UI", () => {
  const page = readProjectFile("src/app/page.tsx");
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");

  assert.match(page, /escapeBlocked=\{accountMenuOpen \|\| activeAccountDialog !== null\}/);
  assert.match(sidebar, /event\.key === "Escape" && isMobile && openMobile && !escapeBlocked/);
});

test("keeps the page session selection callback free of request locks", () => {
  const page = readProjectFile("src/app/page.tsx");
  const selectSession = page.match(/function selectSession\(sessionId: string\) \{([\s\S]*?)\n  \}/);

  assert.ok(selectSession);
  assert.match(selectSession[1], /setActiveSessionId\(sessionId\)/);
  assert.match(selectSession[1], /setDraft\(""\)/);
  assert.match(selectSession[1], /setComposerNotice\(""\)/);
  assert.doesNotMatch(selectSession[1], /pendingSessionId|isLoading|cancellationPending|creatingSession/);
});
