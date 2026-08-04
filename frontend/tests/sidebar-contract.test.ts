import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const projectFile = (path: string) => new URL(`../${path}`, import.meta.url);
const readProjectFile = (path: string) => readFileSync(projectFile(path), "utf8");
const globalStyles = readProjectFile("src/app/globals.css");

function cssBlock(selector: string) {
  const start = globalStyles.indexOf(`${selector} {`);
  assert.notEqual(start, -1, `missing CSS selector: ${selector}`);
  const end = globalStyles.indexOf("}", start);
  assert.notEqual(end, -1, `unterminated CSS selector: ${selector}`);
  return globalStyles.slice(start, end);
}

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
  assert.match(sidebar, /sidebarSurfaceRef\.current\?\.focus\(\)/);
  assert.match(sidebar, /return \(\) => window\.cancelAnimationFrame\(focusDrawer\);/);
});

test("uses the approved localized trigger actions", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  assert.match(sidebar, /"收起侧边栏"/);
  assert.match(sidebar, /"展开侧边栏"/);
  assert.match(sidebar, /"打开聊天记录"/);
  assert.match(sidebar, /"关闭聊天记录"/);
  assert.match(sidebar, /PanelLeft/);
  assert.doesNotMatch(sidebar, /PanelLeftClose|PanelLeftOpen/);
  assert.match(sidebar, /<PanelLeft aria-hidden="true" \/>/);
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
  assert.match(design, /single visible collapse\/expand trigger/);
  assert.match(design, /Sidebar state changes are immediate/);
});

test("composes the Jyotisha app sidebar from the generic shell", () => {
  assert.equal(existsSync(projectFile("src/components/app-sidebar.tsx")), true);
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");

  for (const component of ["SidebarHeader", "SidebarContent", "SidebarFooter", "SidebarRail"]) {
    assert.match(appSidebar, new RegExp(`<${component}\\b`));
  }
});

test("keeps the sidebar brand row free of a duplicate collapse trigger", () => {
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");

  assert.doesNotMatch(appSidebar, /SidebarTrigger/);
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

test("uses portaled Base UI menus with safe collision padding", () => {
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");
  const sessionRow = readProjectFile("src/components/sidebar-session-row.tsx");
  assert.match(appSidebar, /import \{ Menu \} from "@base-ui\/react\/menu"/);
  assert.match(appSidebar, /<Menu\.Portal>/);
  assert.match(appSidebar, /collisionPadding=\{12\}/);
  assert.match(appSidebar, /<Menu\.Popup className="account-menu-popup"/);
  assert.match(sessionRow, /import \{ Menu \} from "@base-ui\/react\/menu"/);
  assert.match(sessionRow, /<Menu\.Portal>/);
  assert.match(sessionRow, /<Menu\.Popup className="session-actions"/);
  assert.doesNotMatch(sessionRow, /role="menu(?:item)?"/);
});

test("closes an open account menu when the sidebar viewport or state changes", () => {
  const appSidebar = readProjectFile("src/components/app-sidebar.tsx");
  assert.match(appSidebar, /const \{[^}]*\bviewport\b[^}]*\} = useSidebar\(\)/);
  assert.match(appSidebar, /const menuPlacement = `\$\{viewport\}:\$\{state\}`/);
  assert.match(appSidebar, /previousMenuPlacement/);
  assert.match(appSidebar, /previousMenuPlacement\.current !== menuPlacement && accountMenuOpen/);
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

test("maps the sidebar semantic aliases and responsive dimensions", () => {
  for (const declaration of [
    "--sidebar-background: var(--color-sidebar);",
    "--sidebar-solid: var(--color-sidebar-solid);",
    "--sidebar-foreground: var(--color-ink);",
    "--sidebar-muted-foreground: var(--color-ink-secondary);",
    "--sidebar-accent: var(--color-selected);",
    "--sidebar-accent-foreground: var(--color-ink);",
    "--sidebar-border: var(--color-border);",
    "--sidebar-ring: var(--color-focus);",
    "--sidebar-primary: var(--color-surface-dark);",
    "--sidebar-primary-foreground: var(--color-on-dark);",
    "--sidebar-width-desktop: 288px;",
    "--sidebar-width-tablet: 240px;",
    "--sidebar-width-icon: 64px;",
    "--sidebar-width-mobile: min(86vw, 320px);",
  ]) {
    assert.equal(globalStyles.includes(declaration), true, `missing ${declaration}`);
  }
});

test("selects desktop and tablet shell widths from provider data", () => {
  assert.match(globalStyles, /\.group\\\/sidebar-provider\[data-viewport\][^{]*\{[^}]*height:\s*100dvh/);
  assert.match(globalStyles, /\[data-viewport="desktop"\]\[data-state="expanded"\]\s+\.chat-app\s*\{[^}]*grid-template-columns:\s*var\(--sidebar-width-desktop\)\s+minmax\(0,\s*1fr\)/);
  assert.match(globalStyles, /\[data-viewport="tablet"\]\[data-state="expanded"\]\s+\.chat-app\s*\{[^}]*grid-template-columns:\s*var\(--sidebar-width-tablet\)\s+minmax\(0,\s*1fr\)/);
  assert.match(globalStyles, /\[data-state="collapsed"\]\s+\.chat-app\s*\{[^}]*grid-template-columns:\s*var\(--sidebar-width-icon\)\s+minmax\(0,\s*1fr\)/);
  assert.doesNotMatch(globalStyles, /transition:[^;}]*\b(?:width|grid-template-columns)\b/);
});

test("changes sidebar state without transition frames", () => {
  const sidebar = readProjectFile("src/components/ui/sidebar.tsx");
  const design = readProjectFile("DESIGN.md");

  assert.doesNotMatch(sidebar, /document\.startViewTransition/);
  assert.doesNotMatch(sidebar, /skipMotion/);
  assert.match(sidebar, /const setOpen = useCallback\(\(nextOpen: boolean\) => \{\s*commitOpen\(nextOpen\);/);
  assert.match(sidebar, /else commitOpen\(!open\);/);
  assert.doesNotMatch(globalStyles, /view-transition-name/);
  assert.doesNotMatch(globalStyles, /::view-transition-/);
  assert.match(globalStyles, /\[data-sidebar="trigger"\]\s+svg\s*\{[^}]*width:\s*18px[^}]*height:\s*18px/);
  assert.doesNotMatch(cssBlock('[data-sidebar="trigger"]'), /transition:/);
  assert.match(globalStyles, /\[data-sidebar="sidebar"\]\[data-mobile-open="false"\][^{]*\{[^}]*visibility:\s*hidden[^}]*transform:\s*translateX\(-100%\)/);
  assert.match(design, /Sidebar state changes are immediate/);
});

test("keeps the chat title in the flexible left-aligned header column", () => {
  assert.match(cssBlock(".chat-header"), /grid-template-columns:\s*auto\s+minmax\(0,\s*1fr\)\s+auto/);
  assert.match(cssBlock(".chat-header"), /text-align:\s*left/);
  assert.doesNotMatch(cssBlock(".chat-header"), /justify-content:\s*space-between/);
});

test("anchors the account footer to the bottom edge without trailing sidebar padding", () => {
  assert.match(globalStyles, /\.sidebar \{ position:[^}]*padding:\s*var\(--space-5\)\s+var\(--space-3\)\s+0/);
  assert.match(cssBlock(".sidebar-footer"), /margin-top:\s*0/);
});

test("makes SidebarContent the only sidebar scroll owner", () => {
  assert.match(cssBlock('[data-sidebar="header"]'), /flex:\s*0\s+0\s+auto/);
  assert.match(cssBlock('[data-sidebar="content"]'), /min-height:\s*0/);
  assert.match(cssBlock('[data-sidebar="content"]'), /overflow-y:\s*auto/);
  assert.match(cssBlock('[data-sidebar="footer"]'), /flex:\s*0\s+0\s+auto/);
  assert.doesNotMatch(cssBlock(".session-list"), /overflow(?:-y)?:\s*auto/);
  assert.match(readProjectFile("src/components/sidebar-session-row.tsx"), /className="session-title"[\s\S]*className="truncate"/);
  assert.match(globalStyles, /\[data-active="true"\][^{]*\{[^}]*background:\s*var\(--sidebar-accent\)/);
});

test("renders each session title and menu as one unified row surface", () => {
  assert.match(cssBlock(".session-row"), /grid-template-columns:\s*minmax\(0,\s*1fr\)\s+44px/);
  assert.match(globalStyles, /\.session-row:has\(\.session-main\[data-active="true"\]\)[^{]*\{[^}]*background:\s*var\(--sidebar-accent\)/);
  assert.match(cssBlock('.session-main[data-active="true"]'), /background:\s*transparent/);
  assert.match(cssBlock(".session-menu-trigger"), /border-radius:\s*0/);
  assert.doesNotMatch(cssBlock(".session-menu-trigger"), /border-radius:\s*50%/);
});

test("styles the non-mobile collapsed rail without repeated session rows", () => {
  assert.match(globalStyles, /@media\s*\(min-width:\s*768px\)[\s\S]*\[data-state="collapsed"\][^{]*\.brand-row/);
  assert.match(globalStyles, /\[data-state="collapsed"\][^{]*\[data-sidebar="menu-button"\][^{]*\{[^}]*width:\s*44px/);
  assert.match(globalStyles, /\[data-state="collapsed"\][^{]*\.profile-trigger[^{]*\{[^}]*width:\s*44px/);
  assert.match(globalStyles, /\[data-sidebar="rail"\][^{]*\{[^}]*position:\s*absolute[^}]*width:\s*var\(--space-2\)/);
  assert.match(globalStyles, /\[data-sidebar="rail"\]:focus-visible[^{]*\{[^}]*outline/);
});

test("uses provider attributes for the mobile drawer and scrim", () => {
  assert.match(globalStyles, /@media\s*\(max-width:\s*767px\)[\s\S]*\.chat-app\s*\{[^}]*grid-template-columns:\s*1fr/);
  assert.match(globalStyles, /\[data-sidebar="sidebar"\][^{]*\{[^}]*position:\s*fixed[^}]*width:\s*var\(--sidebar-width-mobile\)/);
  assert.match(globalStyles, /\[data-sidebar="sidebar"\]\[data-mobile-open="false"\][^{]*\{[^}]*transform:\s*translateX\(-100%\)/);
  assert.match(globalStyles, /\[data-sidebar="sidebar"\]\[data-mobile-open="true"\][^{]*\{[^}]*visibility:\s*visible[^}]*transform:\s*translateX\(0\)/);
  assert.match(globalStyles, /\.sidebar-scrim\s*\{[^}]*position:\s*fixed[^}]*background:\s*var\(--color-scrim\)/);
  assert.match(globalStyles, /\[data-sidebar="sidebar"\]:focus\s*\{[^}]*outline:\s*none/);
  assert.match(globalStyles, /\[data-sidebar="rail"\]\s*\{[^}]*display:\s*none/);
});

test("styles the portaled account popup and collapsed tooltips", () => {
  assert.match(globalStyles, /:has\(>\s*\.account-menu-popup\)[^{]*\{[^}]*z-index:\s*30/);
  assert.match(globalStyles, /\.account-menu-popup\s*\{[^}]*width:\s*min\(280px,\s*calc\(100vw\s*-\s*var\(--space-6\)\)\)[^}]*transform-origin:\s*var\(--transform-origin\)/);
  assert.match(globalStyles, /\.account-menu-popup\[data-starting-style\][^{]*\.account-menu-popup\[data-ending-style\][^{]*\{[^}]*opacity:\s*0[^}]*translateY\(var\(--space-1\)\)/);
  assert.match(globalStyles, /\[role="tooltip"\]\s*\{[^}]*pointer-events:\s*none[^}]*font-size:\s*var\(--type-caption\)/);
  assert.match(globalStyles, /\[role="tooltip"\]\[data-starting-style\][^{]*\{[^}]*opacity:\s*0[^}]*translateX\(-?var\(--space-1\)\)/);
});

test("extends sidebar accessibility preference styles", () => {
  assert.match(globalStyles, /@media\s*\(prefers-reduced-motion:\s*reduce\)[\s\S]*\.account-menu-popup\[data-starting-style\][^{]*\{[^}]*transform:\s*none/);
  assert.match(globalStyles, /@media\s*\(prefers-reduced-transparency:\s*reduce\)[\s\S]*\.sidebar\s*\{[^}]*background:\s*var\(--sidebar-solid\)[^}]*backdrop-filter:\s*none/);
  assert.match(globalStyles, /@media\s*\(prefers-contrast:\s*more\)[\s\S]*\[data-active="true"\]::before\s*\{[^}]*width:\s*var\(--space-1\)/);
});

test("removes class-owned drawer state and obsolete sidebar anchoring", () => {
  assert.doesNotMatch(globalStyles, /\.(?:sidebar-backdrop|sidebar-close|mobile-menu|sidebar-open)\b/);
  assert.doesNotMatch(globalStyles, /\.account-menu\s*\{/);
  assert.doesNotMatch(globalStyles, /\.session-list\s*\{[^}]*overflow(?:-y)?:\s*auto/);
});
