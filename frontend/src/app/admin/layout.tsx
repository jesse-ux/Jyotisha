import { ReactNode } from "react";
import { redirect } from "next/navigation";
import { isAdminEmail } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function AdminLayout({ children }: { children: ReactNode }) {
  if (process.env.NODE_ENV === "development" && process.env.ENABLE_ADMIN_PREVIEW === "1") return children;

  const supabase = await createServerSupabaseClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) redirect("/login");
  if (!isAdminEmail(user.email)) redirect("/");

  return children;
}
