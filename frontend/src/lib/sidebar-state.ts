export type SidebarViewport = "mobile" | "tablet" | "desktop";

type EditableTarget = {
  readonly tagName?: unknown;
  readonly isContentEditable?: unknown;
};

export type SidebarShortcutEvent = Pick<
  KeyboardEvent,
  "key" | "metaKey" | "ctrlKey" | "altKey" | "shiftKey"
> & {
  readonly target: EventTarget | EditableTarget | null;
};

function isEditableTarget(target: SidebarShortcutEvent["target"]): target is EditableTarget {
  return target !== null && typeof target === "object";
}

export function sidebarViewportForWidth(width: number): SidebarViewport {
  if (width < 768) return "mobile";
  if (width < 1024) return "tablet";
  return "desktop";
}

export function defaultSidebarOpen(viewport: SidebarViewport): boolean {
  return viewport === "desktop";
}

export function shouldHandleSidebarShortcut(event: SidebarShortcutEvent): boolean {
  const target = event.target;
  const editable = isEditableTarget(target)
    && (target.isContentEditable === true || /^(INPUT|TEXTAREA|SELECT)$/.test(String(target.tagName ?? "")));

  return !editable
    && event.key.toLowerCase() === "b"
    && (event.metaKey || event.ctrlKey)
    && !event.altKey
    && !event.shiftKey;
}
