"use client";

import {
  AuditOutlined,
  GiftOutlined,
  MessageOutlined,
  TeamOutlined,
  TransactionOutlined,
} from "@ant-design/icons";
import { Authenticated, Refine } from "@refinedev/core";
import { ErrorComponent, ThemedLayout, useNotificationProvider } from "@refinedev/antd";
import routerProvider from "@refinedev/nextjs-router";
import { App as AntdApp, ConfigProvider, Spin, theme } from "antd";
import type { ReactNode } from "react";

import {
  adminAccessControlProvider,
  adminAuthProvider,
  adminDataProvider,
} from "@/lib/admin/providers";

export function AdminApp({ children }: { children: ReactNode }) {
  const notificationProvider = useNotificationProvider();
  return (
    <ConfigProvider theme={{ algorithm: theme.darkAlgorithm, token: { colorPrimary: "#c8a96b" } }}>
      <AntdApp>
        <Refine
          routerProvider={routerProvider}
          dataProvider={adminDataProvider}
          authProvider={adminAuthProvider}
          accessControlProvider={adminAccessControlProvider}
          notificationProvider={notificationProvider}
          resources={[
            { name: "codes", list: "/admin/codes", meta: { label: "兑换码", icon: <GiftOutlined /> } },
            { name: "users", list: "/admin/users", meta: { label: "用户资料", icon: <TeamOutlined /> } },
            { name: "credit-transactions", list: "/admin/credit-transactions", meta: { label: "积分流水", icon: <TransactionOutlined /> } },
            { name: "consultations", list: "/admin/consultations", meta: { label: "咨询请求", icon: <MessageOutlined /> } },
            { name: "audit-logs", list: "/admin/audit-logs", meta: { label: "审计日志", icon: <AuditOutlined /> } },
          ]}
          options={{
            syncWithLocation: true,
            warnWhenUnsavedChanges: true,
            title: { text: "Jyotisha 后台" },
          }}
        >
          <Authenticated
            key="admin-authenticated"
            loading={<div className="admin-loading"><Spin size="large" /><span>正在验证后台权限</span></div>}
          >
            <ThemedLayout>{children}</ThemedLayout>
          </Authenticated>
        </Refine>
      </AntdApp>
    </ConfigProvider>
  );
}

export { ErrorComponent as AdminErrorComponent };
