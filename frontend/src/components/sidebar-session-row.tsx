"use client";

import { Menu } from "@base-ui/react/menu";
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
  return (
    <Menu.Root
      open={sessionMutationMenuVisible(menuOpen, disabled)}
      onOpenChange={onMenuOpenChange}
      modal={false}
      disabled={disabled}
    >
      <div
        className="session-row"
        onContextMenu={(event) => {
          event.preventDefault();
          if (!disabled) onMenuOpenChange(true);
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
        <Menu.Trigger
          className="session-menu-trigger"
          type="button"
          aria-label={`${session.title} 更多操作`}
          disabled={disabled}
        >
          <MoreHorizontal aria-hidden="true" />
        </Menu.Trigger>
      </div>
      <Menu.Portal>
        <Menu.Positioner className="session-actions-positioner" side="bottom" align="end" sideOffset={4} collisionPadding={12}>
          <Menu.Popup className="session-actions" aria-label={`${session.title} 操作`}>
            <Menu.Item className="session-action-item" onClick={onTogglePinned}>
              {session.pinned ? <PinOff aria-hidden="true" /> : <Pin aria-hidden="true" />}
              <span>{session.pinned ? "取消置顶" : "置顶"}</span>
            </Menu.Item>
            <Menu.Item className="session-action-item" onClick={onRename}><Pencil aria-hidden="true" /><span>重命名</span></Menu.Item>
            <Menu.Item className="session-action-item" onClick={onShare}><Share2 aria-hidden="true" /><span>转发</span></Menu.Item>
            <Menu.Item className="session-action-item" onClick={onToggleArchived}>
              {session.archived ? <ArchiveRestore aria-hidden="true" /> : <Archive aria-hidden="true" />}
              <span>{session.archived ? "恢复" : "归档"}</span>
            </Menu.Item>
            <Menu.Separator className="session-actions-separator" />
            <Menu.Item className="session-action-item session-action-danger" onClick={onDelete}><Trash2 aria-hidden="true" /><span>删除</span></Menu.Item>
          </Menu.Popup>
        </Menu.Positioner>
      </Menu.Portal>
    </Menu.Root>
  );
});
