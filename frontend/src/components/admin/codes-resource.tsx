"use client";

import { useCreate, useDelete, useGetIdentity, usePermissions, useUpdate } from "@refinedev/core";
import { Button, DatePicker, Form, Input, InputNumber, Modal, Space, Tag, Typography, type TableColumnsType } from "antd";
import dayjs from "dayjs";
import { useState } from "react";

import { formatAdminDate, ResourceTable } from "@/components/admin/resource-table";
import type { AdminIdentity } from "@/lib/admin/providers";

type CodeRecord = {
  id: string;
  code?: string;
  mask: string;
  credits: number;
  expiresAt: string | null;
  note: string | null;
  createdAt: string;
  redeemedEmail: string | null;
  redeemedAt: string | null;
  revokedAt: string | null;
  status: "available" | "expired" | "redeemed" | "revoked";
};

type CreateValues = {
  credits: number;
  count: number;
  expiresAt?: ReturnType<typeof dayjs>;
  note?: string;
};
type EditValues = { note?: string; expiresAt?: ReturnType<typeof dayjs> | null };

const statusColors: Record<CodeRecord["status"], string> = {
  available: "green",
  expired: "orange",
  redeemed: "blue",
  revoked: "red",
};

export default function CodesPage() {
  const { data: role } = usePermissions<"admin" | "viewer">({});
  const { data: identity } = useGetIdentity<AdminIdentity>();
  const { mutate: createCodes, mutation: createMutation } = useCreate<{ id: string; generated: CodeRecord[] }>();
  const { mutate: updateCode, mutation: updateMutation } = useUpdate<CodeRecord>();
  const { mutate: revokeCode, mutation: revokeMutation } = useDelete<CodeRecord>();
  const [createOpen, setCreateOpen] = useState(false);
  const [editRecord, setEditRecord] = useState<CodeRecord | null>(null);
  const [generated, setGenerated] = useState<CodeRecord[]>([]);
  const [createForm] = Form.useForm<CreateValues>();
  const [editForm] = Form.useForm<EditValues>();
  const writable = role === "admin";

  function submitCreate(values: CreateValues) {
    createCodes({
      resource: "codes",
      values: {
        credits: values.credits,
        count: values.count,
        expiresAt: values.expiresAt?.toISOString() ?? null,
        note: values.note?.trim() || null,
      },
      successNotification: false,
    }, {
      onSuccess(result) {
        setGenerated(result.data.generated);
        setCreateOpen(false);
        createForm.resetFields();
      },
    });
  }

  function submitEdit(values: EditValues) {
    if (!editRecord) return;
    updateCode({
      resource: "codes",
      id: editRecord.id,
      values: {
        note: values.note?.trim() || null,
        expiresAt: values.expiresAt?.toISOString() ?? null,
      },
    }, { onSuccess: () => setEditRecord(null) });
  }

  function confirmRevoke(record: CodeRecord) {
    Modal.confirm({
      title: "撤销此兑换码？",
      content: `${record.mask} 撤销后不可兑换，且不能恢复。`,
      okText: "确认撤销",
      okButtonProps: { danger: true },
      cancelText: "取消",
      onOk: () => new Promise<void>((resolve, reject) => {
        revokeCode({ resource: "codes", id: record.id }, {
          onSuccess: () => resolve(),
          onError: () => reject(new Error("撤销失败")),
        });
      }),
    });
  }

  const columns: TableColumnsType<CodeRecord> = [
    { title: "兑换码", dataIndex: "mask" },
    { title: "点数", dataIndex: "credits", sorter: true },
    { title: "状态", dataIndex: "status", sorter: true, render: (value) => <Tag color={statusColors[value as CodeRecord["status"]]}>{value}</Tag> },
    { title: "到期时间", dataIndex: "expiresAt", sorter: true, render: formatAdminDate },
    { title: "备注", dataIndex: "note", render: (value) => value || "—" },
    { title: "兑换账户", dataIndex: "redeemedEmail", render: (value) => value || "—" },
    { title: "兑换时间", dataIndex: "redeemedAt", render: formatAdminDate },
    { title: "撤销时间", dataIndex: "revokedAt", render: formatAdminDate },
    { title: "创建时间", dataIndex: "createdAt", sorter: true, render: formatAdminDate },
    {
      title: "操作",
      fixed: "right",
      render: (_, record) => writable && record.status !== "redeemed" && record.status !== "revoked" ? (
        <Space>
          <Button size="small" onClick={() => {
            setEditRecord(record);
            editForm.setFieldsValue({
              note: record.note ?? undefined,
              expiresAt: record.expiresAt ? dayjs(record.expiresAt) : null,
            });
          }}>编辑</Button>
          <Button danger size="small" loading={revokeMutation.isPending} onClick={() => confirmRevoke(record)}>撤销</Button>
        </Space>
      ) : "—",
    },
  ];

  return (
    <>
      <ResourceTable<CodeRecord>
        resource="codes"
        title={`兑换码${identity ? ` · ${identity.email} (${identity.role})` : ""}`}
        columns={columns}
        statusOptions={[
          { label: "可用", value: "available" },
          { label: "已过期", value: "expired" },
          { label: "已兑换", value: "redeemed" },
          { label: "已撤销", value: "revoked" },
        ]}
        extra={writable ? <Button type="primary" onClick={() => setCreateOpen(true)}>批量生成</Button> : <Tag>viewer 只读</Tag>}
      />

      <Modal title="批量生成兑换码" open={createOpen} onCancel={() => setCreateOpen(false)} footer={null} destroyOnHidden>
        <Form form={createForm} layout="vertical" initialValues={{ credits: 10, count: 1 }} onFinish={submitCreate}>
          <Form.Item name="credits" label="每个点数" rules={[{ required: true }]}><InputNumber min={1} max={1_000_000} style={{ width: "100%" }} /></Form.Item>
          <Form.Item name="count" label="数量" rules={[{ required: true }]}><InputNumber min={1} max={100} style={{ width: "100%" }} /></Form.Item>
          <Form.Item name="expiresAt" label="到期时间"><DatePicker showTime style={{ width: "100%" }} /></Form.Item>
          <Form.Item name="note" label="备注"><Input maxLength={500} /></Form.Item>
          <Button block type="primary" htmlType="submit" loading={createMutation.isPending}>生成</Button>
        </Form>
      </Modal>

      <Modal title="完整兑换码（仅显示本次）" open={generated.length > 0} onCancel={() => setGenerated([])} footer={<Button onClick={() => setGenerated([])}>我已保存</Button>}>
        <Typography.Paragraph type="warning">关闭后无法再次查看完整兑换码，请立即安全保存。</Typography.Paragraph>
        {generated.map((record) => <Typography.Paragraph copyable key={record.code}><Typography.Text code>{record.code}</Typography.Text></Typography.Paragraph>)}
      </Modal>

      <Modal title="编辑未兑换码" open={Boolean(editRecord)} onCancel={() => setEditRecord(null)} footer={null} destroyOnHidden>
        <Form form={editForm} layout="vertical" onFinish={submitEdit}>
          <Form.Item name="expiresAt" label="到期时间"><DatePicker showTime style={{ width: "100%" }} /></Form.Item>
          <Form.Item name="note" label="备注"><Input maxLength={500} /></Form.Item>
          <Button block type="primary" htmlType="submit" loading={updateMutation.isPending}>保存</Button>
        </Form>
      </Modal>
    </>
  );
}
