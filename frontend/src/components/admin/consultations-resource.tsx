"use client";

import { Tag, type TableColumnsType } from "antd";

import { formatAdminDate, ResourceTable } from "@/components/admin/resource-table";

type ConsultationRecord = {
  id: string;
  email: string | null;
  requestId: string;
  status: string;
  createdAt: string;
  updatedAt: string;
};

const colors: Record<string, string> = {
  reserved: "gold",
  completed: "green",
  cancelled: "default",
};
const columns: TableColumnsType<ConsultationRecord> = [
  { title: "用户", dataIndex: "email", render: (value) => value || "—" },
  { title: "请求 ID", dataIndex: "requestId" },
  { title: "状态", dataIndex: "status", sorter: true, render: (value) => <Tag color={colors[value]}>{value}</Tag> },
  { title: "创建时间", dataIndex: "createdAt", sorter: true, render: formatAdminDate },
  { title: "更新时间", dataIndex: "updatedAt", sorter: true, render: formatAdminDate },
];

export default function ConsultationsPage() {
  return <ResourceTable<ConsultationRecord>
    resource="consultations"
    title="咨询请求（只读）"
    columns={columns}
    statusOptions={[
      { label: "已预扣", value: "reserved" },
      { label: "已完成", value: "completed" },
      { label: "已取消", value: "cancelled" },
    ]}
  />;
}
