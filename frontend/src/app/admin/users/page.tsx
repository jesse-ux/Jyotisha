"use client";

import { Tag, type TableColumnsType } from "antd";

import { formatAdminDate, ResourceTable } from "@/components/admin/resource-table";

type UserRecord = {
  id: string;
  email: string;
  name: string | null;
  role: string;
  emailVerified: boolean;
  banned: boolean;
  createdAt: string;
  credits: number;
  birthDate: string | null;
  birthTimeStatus: string | null;
  birthPlace: string | null;
};

const columns: TableColumnsType<UserRecord> = [
  { title: "邮箱", dataIndex: "email", sorter: true },
  { title: "姓名", dataIndex: "name", sorter: true, render: (value) => value || "—" },
  { title: "角色", dataIndex: "role", render: (value) => <Tag>{value}</Tag> },
  { title: "积分", dataIndex: "credits", sorter: true },
  { title: "出生日期", dataIndex: "birthDate", render: (value) => value || "—" },
  { title: "出生时间状态", dataIndex: "birthTimeStatus", render: (value) => value || "—" },
  { title: "出生地", dataIndex: "birthPlace", render: (value) => value || "—" },
  { title: "邮箱验证", dataIndex: "emailVerified", render: (value) => value ? "已验证" : "未验证" },
  { title: "状态", dataIndex: "banned", render: (value) => value ? <Tag color="red">已禁用</Tag> : <Tag color="green">正常</Tag> },
  { title: "注册时间", dataIndex: "createdAt", sorter: true, render: formatAdminDate },
];

export default function UsersPage() {
  return <ResourceTable<UserRecord> resource="users" title="用户资料（只读）" columns={columns} />;
}
