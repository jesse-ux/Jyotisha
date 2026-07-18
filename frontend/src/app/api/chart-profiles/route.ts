import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";

type ChartProfilePayload = {
  id?: string;
  role?: "self" | "other";
  profile?: unknown;
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
      .from("chart_profiles")
      .select("id, role, profile, updated_at")
      .eq("user_id", user.id)
      .order("updated_at", { ascending: false });

    if (error) throw error;
    return NextResponse.json({ profiles: data ?? [] });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: errorMessage(error, "星盘库暂时不可用") }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const supabase = await createServerSupabaseClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return NextResponse.json({ error: "请先登录" }, { status: 401 });

    const body = await request.json().catch(() => null) as ChartProfilePayload | null;
    if (!body?.profile || typeof body.profile !== "object") {
      return NextResponse.json({ error: "星盘资料格式不正确" }, { status: 400 });
    }
    const role = body.role === "self" ? "self" : "other";
    const updatedAt = new Date().toISOString();
    let data;
    let error;
    if (role === "self") {
      const existing = await supabase
        .from("chart_profiles")
        .select("id")
        .eq("user_id", user.id)
        .eq("role", "self")
        .maybeSingle();
      if (existing.error) throw existing.error;
      const query = existing.data?.id
        ? supabase
          .from("chart_profiles")
          .update({ profile: body.profile, updated_at: updatedAt })
          .eq("id", existing.data.id)
          .select("id, role, profile, updated_at")
          .single()
        : supabase
          .from("chart_profiles")
          .insert({ user_id: user.id, role, profile: body.profile, updated_at: updatedAt })
          .select("id, role, profile, updated_at")
          .single();
      ({ data, error } = await query);
    } else {
      const record = {
        ...(body.id ? { id: body.id } : {}),
        user_id: user.id,
        role,
        profile: body.profile,
        updated_at: updatedAt,
      };
      ({ data, error } = await supabase
        .from("chart_profiles")
        .upsert(record, { onConflict: "id" })
        .select("id, role, profile, updated_at")
        .single());
    }

    if (error) throw error;
    return NextResponse.json({ profile: data });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: errorMessage(error, "星盘保存失败") }, { status: 500 });
  }
}
