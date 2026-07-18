import { NextResponse } from "next/server";
import { createAdminSupabaseClient, isAdminEmail } from "@/lib/supabase/admin";
import {
  isSupabaseConfigurationError,
} from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

type ProfilePatchPayload = {
  name?: unknown;
  birth_date?: unknown;
  birth_time?: unknown;
  country_code?: unknown;
  province_code?: unknown;
  city_code?: unknown;
  district_code?: unknown;
  latitude?: unknown;
  longitude?: unknown;
  timezone_offset?: unknown;
};

function nullableString(value: unknown) {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function nullableNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function isMissingProfileColumn(error: { code?: string; message?: string } | null) {
  const message = error?.message?.toLowerCase() ?? "";
  return error?.code === "PGRST204"
    || error?.code === "42703"
    || message.includes("schema cache")
    || message.includes("column");
}

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

export async function PATCH(request: Request) {
  try {
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "请先登录" }, { status: 401 });
    }

    const payload = await request.json().catch(() => null) as ProfilePatchPayload | null;
    if (!payload || typeof payload !== "object") {
      return NextResponse.json({ error: "账户资料格式不正确" }, { status: 400 });
    }

    const admin = createAdminSupabaseClient();
    const baseProfile = {
      id: user.id,
      name: nullableString(payload.name),
      birth_date: nullableString(payload.birth_date),
      birth_time: nullableString(payload.birth_time),
      country_code: nullableString(payload.country_code),
      province_code: nullableString(payload.province_code),
      city_code: nullableString(payload.city_code),
      district_code: nullableString(payload.district_code),
      updated_at: new Date().toISOString(),
    };
    const withCoordinates = {
      ...baseProfile,
      latitude: nullableNumber(payload.latitude),
      longitude: nullableNumber(payload.longitude),
      timezone_offset: nullableNumber(payload.timezone_offset),
    };
    const withoutCoordinates = baseProfile;
    let { data, error } = await admin
      .from("profiles")
      .upsert(withCoordinates, { onConflict: "id" })
      .select("id")
      .single();
    if (error && isMissingProfileColumn(error)) {
      const fallback = await admin
        .from("profiles")
        .upsert(withoutCoordinates, { onConflict: "id" })
        .select("id")
        .single();
      data = fallback.data;
      error = fallback.error;
    }

    if (error || !data) {
      return NextResponse.json({ error: "暂时无法保存账户资料" }, { status: 500 });
    }

    return NextResponse.json({ ok: true });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: "账户服务暂时不可用" }, { status: 500 });
  }
}
