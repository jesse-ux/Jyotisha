import "@refinedev/antd/dist/reset.css";
import "antd/dist/reset.css";
import type { ReactNode } from "react";

import { AdminApp } from "@/components/admin/admin-app";

export const dynamic = "force-dynamic";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminApp>{children}</AdminApp>;
}
