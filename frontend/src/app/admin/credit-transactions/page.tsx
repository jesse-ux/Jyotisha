"use client";

import { Tag, type TableColumnsType } from "antd";

import { formatAdminDate, ResourceTable } from "@/components/admin/resource-table";

type TransactionRecord = {
  id: string;
  email: string | null;
  type: string;
  amount: number;
  balanceAfter: number;
  requestId: string;
  model: string | null;
  inputTokens: number | null;
  outputTokens: number | null;
  createdAt: string;
};

const columns: TableColumnsType<TransactionRecord> = [
  { title: "用户", dataIndex: "email", render: (value) => value || "—" },
  { title: "类型", dataIndex: "type", sorter: true, render: (value) => <Tag>{value}</Tag> },
  { title: "变动", dataIndex: "amount", sorter: true, render: (value) => value > 0 ? `+${value}` : value },
  { title: "余额", dataIndex: "balanceAfter", sorter: true },
  { title: "请求 ID", dataIndex: "requestId" },
  { title: "模型", dataIndex: "model", render: (value) => value || "—" },
  { title: "输入/输出 token", render: (_, row) => `${row.inputTokens ?? "—"} / ${row.outputTokens ?? "—"}` },
  { title: "时间", dataIndex: "createdAt", sorter: true, render: formatAdminDate },
];

export default function CreditTransactionsPage() {
  return <ResourceTable<TransactionRecord>
    resource="credit-transactions"
    title="积分流水（只读）"
    columns={columns}
    statusOptions={[
      { label: "兑换", value: "redeem" },
      { label: "预扣", value: "reserve" },
      { label: "退款", value: "refund" },
    ]}
  />;
}
