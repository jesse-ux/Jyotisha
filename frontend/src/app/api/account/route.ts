import { NextResponse } from "next/server";
import {
  parseRectificationPriceCredits,
  type AccountRectificationCaseState,
} from "@/lib/birth-time-consultation-consent";
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
  reported_birth_time?: unknown;
  birth_time_source?: unknown;
  birth_time_period?: unknown;
  birth_time_clue?: unknown;
  uncertainty_before_minutes?: unknown;
  uncertainty_after_minutes?: unknown;
  country_code?: unknown;
  province_code?: unknown;
  city_code?: unknown;
  district_code?: unknown;
  latitude?: unknown;
  longitude?: unknown;
  timezone_offset?: unknown;
};

const birthTimeSources = ["hospital_record", "family_exact", "approximate", "period_only", "unknown", "legacy_import"] as const;
const birthTimePeriods = ["early_morning", "morning", "afternoon", "evening", "late_night"] as const;
const rectificationStatuses = ["starting", "active", "paused", "confirming", "completed", "abandoned"] as const;

function nullableString(value: unknown) {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function nullableNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function nullableInteger(value: unknown) {
  return typeof value === "number" && Number.isInteger(value) ? value : null;
}

function nullableChoice(value: unknown, choices: readonly string[]) {
  return typeof value === "string" && choices.includes(value) ? value : null;
}

function isMissingProfileColumn(error: { code?: string; message?: string } | null) {
  const message = error?.message?.toLowerCase() ?? "";
  return error?.code === "PGRST204"
    || error?.code === "42703"
    || message.includes("schema cache")
    || message.includes("column");
}

function projectRectificationCase(value: unknown): AccountRectificationCaseState | null {
  if (value === null || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  const status = rectificationStatuses.find((candidate) => candidate === row.status);
  if (typeof row.id !== "string"
    || row.journey_protocol !== "conversational-evidence-v3"
    || !status
    || typeof row.turn_version !== "number"
    || !Number.isSafeInteger(row.turn_version)
    || row.turn_version < 0) {
    throw new Error("invalid rectification case projection");
  }
  return Object.freeze({
    caseId: row.id,
    journeyProtocol: "conversational-evidence-v3",
    status,
    turnVersion: row.turn_version,
    isRevision: typeof row.revision_of_case_id === "string",
    preservesActiveTime: typeof row.baseline_active_time === "string",
  });
}

export async function GET() {
  try {
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "请先登录" }, { status: 401 });
    }

    const rectificationPriceCredits = parseRectificationPriceCredits(
      process.env.RECTIFICATION_PRICE_CREDITS,
    );
    const { data: profile, error } = await supabase
      .from("profiles")
      .select("credits,active_birth_time,birth_time_status")
      .eq("id", user.id)
      .single();

    if (error) {
      return NextResponse.json({ error: "暂时无法读取账户余额" }, { status: 500 });
    }

    const admin = createAdminSupabaseClient();
    const { data: rectificationCaseRow, error: rectificationCaseError } = await admin
      .from("birth_time_rectification_cases")
      .select("id,journey_protocol,status,turn_version,revision_of_case_id,baseline_active_time,updated_at")
      .eq("user_id", user.id)
      .eq("journey_protocol", "conversational-evidence-v3")
      .order("updated_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (rectificationCaseError) {
      return NextResponse.json({ error: "暂时无法读取生时校正状态" }, { status: 500 });
    }
    const rectificationCase = projectRectificationCase(rectificationCaseRow);

    return NextResponse.json({
      user: { id: user.id, email: user.email ?? null },
      credits: profile.credits,
      isAdmin: isAdminEmail(user.email),
      rectificationPriceCredits,
      hasConfirmedBirthTime: profile.birth_time_status === "confirmed"
        && typeof profile.active_birth_time === "string",
      rectificationCase,
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
      reported_birth_time: nullableString(payload.reported_birth_time),
      birth_time_source: nullableChoice(payload.birth_time_source, birthTimeSources),
      birth_time_period: nullableChoice(payload.birth_time_period, birthTimePeriods),
      birth_time_clue: nullableString(payload.birth_time_clue),
      uncertainty_before_minutes: nullableInteger(payload.uncertainty_before_minutes),
      uncertainty_after_minutes: nullableInteger(payload.uncertainty_after_minutes),
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
