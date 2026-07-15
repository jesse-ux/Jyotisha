import { NextResponse } from "next/server";
import { isAdminEmail } from "@/lib/supabase/admin";
import {
  isSupabaseConfigurationError,
} from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

export async function GET() {
  try {
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "请先登录" }, { status: 401 });
    }

    const { data: profile, error } = await supabase
      .from("profiles")
      .select("credits")
      .eq("id", user.id)
      .single();

    if (error) {
      return NextResponse.json({ error: "暂时无法读取账户余额" }, { status: 500 });
    }

    return NextResponse.json({
      user: { id: user.id, email: user.email ?? null },
      credits: profile.credits,
      isAdmin: isAdminEmail(user.email),
    });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: "账户服务暂时不可用" }, { status: 500 });
  }
}
