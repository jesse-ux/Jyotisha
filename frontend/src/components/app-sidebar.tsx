"use client";

import { Popover } from "@base-ui/react/popover";
import Link from "next/link";
import {
  ChevronRight,
  Gift,
  KeyRound,
  LogOut,
  MessageSquareText,
  Plus,
  UserRound,
} from "lucide-react";
import { useEffect, useRef } from "react";
import type { Ref } from "react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  SidebarSessionRow,
  type SidebarSession,
  type SidebarSessionControls,
} from "@/components/sidebar-session-row";

export type SidebarAccount = {
  name: string;
  email: string;
  credits: number;
  isAdmin: boolean;
  initial: string;
};

export type AppSidebarProps = {
  sessions: readonly SidebarSession[];
  activeSessionId: string | null;
  account: SidebarAccount;
  accountMenuOpen: boolean;
  accountTriggerRef: Ref<HTMLButtonElement>;
  newChatDisabled: boolean;
  creatingSession: boolean;
  sessionControls: SidebarSessionControls;
  onAccountMenuOpenChange: (open: boolean) => void;
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
  onOpenProfile: () => void;
  onOpenRedeem: () => void;
  onOpenLogout: () => void;
};

export function AppSidebar({
  sessions,
  activeSessionId,
  account,
  accountMenuOpen,
  accountTriggerRef,
  newChatDisabled,
  creatingSession,
  sessionControls,
  onAccountMenuOpenChange,
  onNewChat,
  onSelectSession,
  onOpenProfile,
  onOpenRedeem,
  onOpenLogout,
}: AppSidebarProps) {
  const { isMobile, setOpen, setOpenMobile, state, viewport } = useSidebar();
  const firstSessionRef = useRef<HTMLButtonElement>(null);
  const historyHeadingRef = useRef<HTMLHeadingElement>(null);
  const isCollapsedDesktop = state === "collapsed" && !isMobile;
  const showExpandedContent = !isCollapsedDesktop;
  const popoverPlacement = `${viewport}:${state}`;
  const previousPopoverPlacement = useRef(popoverPlacement);

  useEffect(() => {
    if (previousPopoverPlacement.current !== popoverPlacement && accountMenuOpen) {
      onAccountMenuOpenChange(false);
    }
    previousPopoverPlacement.current = popoverPlacement;
  }, [accountMenuOpen, onAccountMenuOpenChange, popoverPlacement]);

  function handleNewChat() {
    onNewChat();
    if (isMobile) setOpenMobile(false);
  }

  function handleExpandHistory() {
    setOpen(true);
    window.requestAnimationFrame(() => {
      (firstSessionRef.current ?? historyHeadingRef.current)?.focus();
    });
  }

  function handleAccountAction(action: () => void) {
    onAccountMenuOpenChange(false);
    action();
  }

  return (
    <Sidebar className="sidebar" aria-label="对话导航">
      <SidebarHeader className="sidebar-header">
        <div className="brand-row">
          <span className="brand-mark" aria-hidden="true" />
          {showExpandedContent ? <strong>Jyotisha</strong> : null}
          <SidebarTrigger placement="sidebar" />
        </div>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              className="new-chat"
              type="button"
              tooltip="新对话"
              disabled={newChatDisabled}
              onClick={handleNewChat}
            >
              <Plus aria-hidden="true" />
              {showExpandedContent ? <span>{creatingSession ? "正在创建" : "新对话"}</span> : null}
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        {showExpandedContent ? (
          <SidebarGroup className="session-nav" aria-label="聊天记录">
            <div className="session-nav-header">
              <SidebarGroupLabel className="sidebar-label" ref={historyHeadingRef} tabIndex={-1}>
                {sessionControls.showingArchived ? "归档记录" : "聊天记录"}
              </SidebarGroupLabel>
              <button className="session-nav-toggle" type="button" onClick={sessionControls.onToggleArchivedView}>
                {sessionControls.showingArchived ? "返回" : `归档 ${sessionControls.archivedCount}`}
              </button>
            </div>
            <SidebarGroupContent>
              {sessions.length === 0 ? <p className="sidebar-empty">暂无对话</p> : (
                <SidebarMenu className="session-list">
                  {sessions.map((session, index) => (
                    <SidebarMenuItem key={session.id}>
                      <SidebarSessionRow
                        ref={index === 0 ? firstSessionRef : undefined}
                        session={session}
                        active={session.id === activeSessionId}
                        disabled={sessionControls.disabled}
                        menuOpen={sessionControls.menuSessionId === session.id}
                        onMenuOpenChange={(open) => sessionControls.onMenuSessionChange(open ? session.id : null)}
                        onSelect={() => {
                          onSelectSession(session.id);
                          if (isMobile) setOpenMobile(false);
                        }}
                        onTogglePinned={() => sessionControls.onTogglePinned(session.id)}
                        onRename={() => sessionControls.onRename(session.id)}
                        onShare={() => sessionControls.onShare(session.id)}
                        onToggleArchived={() => sessionControls.onToggleArchived(session.id)}
                        onDelete={() => sessionControls.onDelete(session.id)}
                      />
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              )}
            </SidebarGroupContent>
          </SidebarGroup>
        ) : (
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                type="button"
                tooltip="聊天记录"
                aria-label="聊天记录"
                onClick={handleExpandHistory}
              >
                <MessageSquareText aria-hidden="true" />
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        )}
      </SidebarContent>

      <SidebarFooter className="sidebar-footer">
        <Popover.Root open={accountMenuOpen} onOpenChange={onAccountMenuOpenChange}>
          <Popover.Trigger
            className="profile-trigger"
            ref={accountTriggerRef}
            type="button"
            aria-haspopup="menu"
          >
            <span className="profile-initial" aria-hidden="true">{account.initial}</span>
            {showExpandedContent ? <span><b>{account.name}</b></span> : null}
            {showExpandedContent ? <ChevronRight className={accountMenuOpen ? "chevron is-open" : "chevron"} aria-hidden="true" /> : null}
          </Popover.Trigger>
          <Popover.Portal>
            <Popover.Positioner
              side={isMobile || state === "expanded" ? "top" : "right"}
              align={isMobile || state === "expanded" ? "end" : "center"}
              sideOffset={8}
              collisionPadding={12}
            >
              <Popover.Popup className="account-menu-popup" role="menu" aria-label="账户菜单">
                <div className="account-menu-identity">
                  <span className="account-menu-avatar" aria-hidden="true">{account.initial}</span>
                  <span><b>{account.name}</b><small>{account.email}</small></span>
                </div>
                <button className="account-menu-item" role="menuitem" type="button" onClick={() => handleAccountAction(onOpenProfile)}>
                  <UserRound aria-hidden="true" /><span>个人资料</span><ChevronRight aria-hidden="true" />
                </button>
                <button className="account-menu-item" role="menuitem" type="button" onClick={() => handleAccountAction(onOpenRedeem)}>
                  <Gift aria-hidden="true" /><span>兑换点数</span><small>{account.credits} 点</small>
                </button>
                {account.isAdmin && <Link className="account-menu-item" href="/admin/codes" role="menuitem" onClick={() => onAccountMenuOpenChange(false)}>
                  <KeyRound aria-hidden="true" /><span>管理兑换码</span><ChevronRight aria-hidden="true" />
                </Link>}
                <div className="account-menu-separator" role="separator" />
                <button className="account-menu-item account-menu-danger" role="menuitem" type="button" onClick={() => handleAccountAction(onOpenLogout)}>
                  <LogOut aria-hidden="true" /><span>退出登录</span>
                </button>
              </Popover.Popup>
            </Popover.Positioner>
          </Popover.Portal>
        </Popover.Root>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
