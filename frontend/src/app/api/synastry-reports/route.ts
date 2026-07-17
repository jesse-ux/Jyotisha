import { NextResponse } from "next/server";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

type SynastryReportPayload = {
  id?: string;
  partnerName?: string;
  report?: unknown;
};

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export async function GET() {
  try {
    const supabase = await createServerSupabaseClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return NextResponse.json({ error: "请先登录" }, { status: 401 });

    const { data, error } = await supabase
      .from("synastry_reports")
      .select("id, partner_name, report, created_at")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false })
      .limit(10);

    if (error) throw error;
    return NextResponse.json({ reports: data ?? [] });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: errorMessage(error, "合盘历史暂时不可用") }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => null) as SynastryReportPayload | null;
    if (!body?.report || typeof body.report !== "object" || Array.isArray(body.report)) {
      return NextResponse.json({ error: "合盘报告格式不正确" }, { status: 400 });
    }

    const supabase = await createServerSupabaseClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return NextResponse.json({ error: "请先登录" }, { status: 401 });

    const partnerName = body.partnerName?.trim() || "对方";
    const record = {
      ...(body.id ? { id: body.id } : {}),
      user_id: user.id,
      partner_name: partnerName,
      report: body.report,
      created_at: new Date().toISOString(),
    };

    const { data, error } = await supabase
      .from("synastry_reports")
      .insert(record)
      .select("id, partner_name, report, created_at")
      .single();

    if (error) throw error;
    return NextResponse.json({ report: data });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: errorMessage(error, "合盘历史保存失败") }, { status: 500 });
  }
}
