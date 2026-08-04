"use client";

import { Menu } from "@base-ui/react/menu";
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
  const menuPlacement = `${viewport}:${state}`;
  const previousMenuPlacement = useRef(menuPlacement);

  useEffect(() => {
    if (previousMenuPlacement.current !== menuPlacement && accountMenuOpen) {
      onAccountMenuOpenChange(false);
    }
    previousMenuPlacement.current = menuPlacement;
  }, [accountMenuOpen, menuPlacement, onAccountMenuOpenChange]);

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

  return (
    <Sidebar className="sidebar" aria-label="对话导航">
      <SidebarHeader className="sidebar-header">
        <div className="brand-row">
          <span className="brand-mark" aria-hidden="true" />
          {showExpandedContent ? <strong>Jyotisha</strong> : null}
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
        <Menu.Root open={accountMenuOpen} onOpenChange={onAccountMenuOpenChange} modal={false}>
          <Menu.Trigger
            className="profile-trigger"
            ref={accountTriggerRef}
            type="button"
          >
            <span className="profile-initial" aria-hidden="true">{account.initial}</span>
            {showExpandedContent ? <span><b>{account.name}</b></span> : null}
            {showExpandedContent ? <ChevronRight className={accountMenuOpen ? "chevron is-open" : "chevron"} aria-hidden="true" /> : null}
          </Menu.Trigger>
          <Menu.Portal>
            <Menu.Positioner
              side={isMobile || state === "expanded" ? "top" : "right"}
              align={isMobile || state === "expanded" ? "end" : "center"}
              sideOffset={8}
              collisionPadding={12}
            >
              <Menu.Popup className="account-menu-popup" aria-label="账户菜单">
                <div className="account-menu-identity">
                  <span className="account-menu-avatar" aria-hidden="true">{account.initial}</span>
                  <span><b>{account.name}</b><small>{account.email}</small></span>
                </div>
                <Menu.Item className="account-menu-item" onClick={onOpenProfile}>
                  <UserRound aria-hidden="true" /><span>个人资料</span><ChevronRight aria-hidden="true" />
                </Menu.Item>
                <Menu.Item className="account-menu-item" onClick={onOpenRedeem}>
                  <Gift aria-hidden="true" /><span>兑换点数</span><small>{account.credits} 点</small>
                </Menu.Item>
                {account.isAdmin && <Menu.LinkItem className="account-menu-item" render={<Link href="/admin/codes" />} closeOnClick>
                  <KeyRound aria-hidden="true" /><span>管理兑换码</span><ChevronRight aria-hidden="true" />
                </Menu.LinkItem>}
                <Menu.Separator className="account-menu-separator" />
                <Menu.Item className="account-menu-item account-menu-danger" onClick={onOpenLogout}>
                  <LogOut aria-hidden="true" /><span>退出登录</span>
                </Menu.Item>
              </Menu.Popup>
            </Menu.Positioner>
          </Menu.Portal>
        </Menu.Root>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
