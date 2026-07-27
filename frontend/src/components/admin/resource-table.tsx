"use client";

import type { BaseRecord } from "@refinedev/core";
import { List, useTable } from "@refinedev/antd";
import { Alert, Empty, Form, Input, Select, Space, Table, type TableColumnsType } from "antd";
import type { ReactNode } from "react";

export type ResourceFilterOption = { label: string; value: string };

export function ResourceTable<T extends BaseRecord>({
  resource,
  title,
  columns,
  statusOptions,
  extra,
}: {
  resource: string;
  title: string;
  columns: TableColumnsType<T>;
  statusOptions?: ResourceFilterOption[];
  extra?: ReactNode;
}) {
  const { tableProps, searchFormProps, tableQuery } = useTable<T, { message: string; statusCode: number }, { q?: string; status?: string }>({
    resource,
    syncWithLocation: true,
    pagination: { pageSize: 20 },
    onSearch(values) {
      return [
        { field: "q", operator: "contains", value: values.q },
        { field: "status", operator: "eq", value: values.status },
      ];
    },
  });

  const error = tableQuery.error;
  return (
    <List title={title} headerButtons={extra}>
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Form {...searchFormProps} layout="inline">
          <Form.Item name="q"><Input.Search allowClear placeholder="搜索" /></Form.Item>
          {statusOptions && (
            <Form.Item name="status">
              <Select allowClear placeholder="状态" options={statusOptions} style={{ minWidth: 160 }} />
            </Form.Item>
          )}
        </Form>
        {error && <Alert type="error" showIcon message="读取失败" description={error.message} />}
        <Table<T>
          {...tableProps}
          columns={columns}
          rowKey="id"
          locale={{ emptyText: <Empty description="暂无数据" /> }}
          scroll={{ x: "max-content" }}
        />
      </Space>
    </List>
  );
}

export function formatAdminDate(value: string | null | undefined) {
  return value ? new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value)) : "—";
}
