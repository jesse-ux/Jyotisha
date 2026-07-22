"use client";

import {
  Archive,
  ArchiveRestore,
  MoreHorizontal,
  Pencil,
  Pin,
  PinOff,
  Share2,
  Trash2,
} from "lucide-react";
import { forwardRef } from "react";
import { SidebarMenuButton } from "@/components/ui/sidebar";
import { sessionMutationMenuVisible } from "@/lib/chat-session-persistence";

export type SidebarSession = {
  readonly id: string;
  readonly title: string;
  readonly messageCount: number;
  readonly pinned: boolean;
  readonly archived: boolean;
};

export type SidebarSessionControls = {
  readonly archivedCount: number;
  readonly showingArchived: boolean;
  readonly menuSessionId: string | null;
  readonly disabled: boolean;
  readonly onToggleArchivedView: () => void;
  readonly onMenuSessionChange: (sessionId: string | null) => void;
  readonly onTogglePinned: (sessionId: string) => void;
  readonly onRename: (sessionId: string) => void;
  readonly onShare: (sessionId: string) => void;
  readonly onToggleArchived: (sessionId: string) => void;
  readonly onDelete: (sessionId: string) => void;
};

type SidebarSessionRowProps = {
  readonly session: SidebarSession;
  readonly active: boolean;
  readonly disabled: boolean;
  readonly menuOpen: boolean;
  readonly onMenuOpenChange: (open: boolean) => void;
  readonly onSelect: () => void;
  readonly onTogglePinned: () => void;
  readonly onRename: () => void;
  readonly onShare: () => void;
  readonly onToggleArchived: () => void;
  readonly onDelete: () => void;
};

export const SidebarSessionRow = forwardRef<HTMLButtonElement, SidebarSessionRowProps>(function SidebarSessionRow({
  session,
  active,
  disabled,
  menuOpen,
  onMenuOpenChange,
  onSelect,
  onTogglePinned,
  onRename,
  onShare,
  onToggleArchived,
  onDelete,
}, ref) {
  function runAction(action: () => void) {
    onMenuOpenChange(false);
    action();
  }

  return (
    <div
      className="session-row"
      onContextMenu={(event) => {
        event.preventDefault();
        if (!disabled) onMenuOpenChange(!menuOpen);
      }}
    >
      <SidebarMenuButton
        ref={ref}
        className="session-main"
        type="button"
        isActive={active}
        aria-current={active ? "page" : undefined}
        disabled={disabled}
        onClick={onSelect}
      >
        <span className="session-title">
          {session.pinned ? <Pin aria-label="已置顶" /> : null}
          <span className="truncate">{session.title}</span>
        </span>
        {session.messageCount > 0 ? <small>{session.messageCount} 条消息</small> : null}
      </SidebarMenuButton>
      <button
        className="session-menu-trigger"
        type="button"
        aria-label={`${session.title} 更多操作`}
        aria-expanded={menuOpen}
        disabled={disabled}
        onClick={() => onMenuOpenChange(!menuOpen)}
      >
        <MoreHorizontal aria-hidden="true" />
      </button>
      {sessionMutationMenuVisible(menuOpen, disabled) ? (
        <div className="session-actions" role="menu" aria-label={`${session.title} 操作`}>
          <button type="button" role="menuitem" onClick={() => runAction(onTogglePinned)}>
            {session.pinned ? <PinOff aria-hidden="true" /> : <Pin aria-hidden="true" />}
            <span>{session.pinned ? "取消置顶" : "置顶"}</span>
          </button>
          <button type="button" role="menuitem" onClick={() => runAction(onRename)}><Pencil aria-hidden="true" /><span>重命名</span></button>
          <button type="button" role="menuitem" onClick={() => runAction(onShare)}><Share2 aria-hidden="true" /><span>转发</span></button>
          <button type="button" role="menuitem" onClick={() => runAction(onToggleArchived)}>
            {session.archived ? <ArchiveRestore aria-hidden="true" /> : <Archive aria-hidden="true" />}
            <span>{session.archived ? "恢复" : "归档"}</span>
          </button>
          <button className="session-action-danger" type="button" role="menuitem" onClick={() => runAction(onDelete)}><Trash2 aria-hidden="true" /><span>删除</span></button>
        </div>
      ) : null}
    </div>
  );
});
