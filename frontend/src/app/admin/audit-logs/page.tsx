"use client";

import { Descriptions, Tag, type TableColumnsType } from "antd";

import { formatAdminDate, ResourceTable } from "@/components/admin/resource-table";

type AuditRecord = {
  id: string;
  actorEmail: string;
  actorRole: string;
  action: string;
  targetId: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  requestId: string;
  createdAt: string;
};

const columns: TableColumnsType<AuditRecord> = [
  { title: "操作者", dataIndex: "actorEmail", sorter: true },
  { title: "角色", dataIndex: "actorRole", render: (value) => <Tag>{value}</Tag> },
  { title: "动作", dataIndex: "action", sorter: true },
  { title: "目标 ID", dataIndex: "targetId" },
  { title: "Request ID", dataIndex: "requestId" },
  { title: "时间", dataIndex: "createdAt", sorter: true, render: formatAdminDate },
];

export default function AuditLogsPage() {
  return <ResourceTable<AuditRecord>
    resource="audit-logs"
    title="审计日志（只读）"
    columns={columns}
    statusOptions={[
      { label: "生成兑换码", value: "redemption_code.create" },
      { label: "修改兑换码", value: "redemption_code.update" },
      { label: "撤销兑换码", value: "redemption_code.revoke" },
    ]}
    extra={<Descriptions size="small" items={[{ key: "policy", label: "策略", children: "仅保存脱敏前后值；日志只追加" }]} />}
  />;
}
