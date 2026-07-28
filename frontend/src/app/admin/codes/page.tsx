"use client";

import { useSearchParams } from "next/navigation";

import AuditLogsResource from "@/components/admin/audit-logs-resource";
import CodesResource from "@/components/admin/codes-resource";
import ConsultationsResource from "@/components/admin/consultations-resource";
import CreditTransactionsResource from "@/components/admin/credit-transactions-resource";
import UsersResource from "@/components/admin/users-resource";

const resourceComponents = {
  codes: CodesResource,
  users: UsersResource,
  "credit-transactions": CreditTransactionsResource,
  consultations: ConsultationsResource,
  "audit-logs": AuditLogsResource,
} as const;

export default function AdminResourcesPage() {
  const requested = useSearchParams().get("resource") ?? "codes";
  const Resource = resourceComponents[
    requested in resourceComponents
      ? requested as keyof typeof resourceComponents
      : "codes"
  ];
  return <Resource />;
}
