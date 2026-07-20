import { NextResponse } from "next/server";
import {
  parseRectificationPriceCredits,
  type AccountRectificationCaseState,
} from "@/lib/birth-time-consultation-consent";
import {
  accountProfilePatchSchema,
  applyAccountProfileConcurrencyGuards,
  resolveAccountBirthTimeApplicationPatch,
} from "@/lib/account-profile-patch";
import { createAdminSupabaseClient, isAdminEmail } from "@/lib/supabase/admin";
import {
  isSupabaseConfigurationError,
} from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

const rectificationStatuses = ["starting", "active", "paused", "confirming", "completed", "abandoned"] as const;

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
    const userId = user.id;

    const rectificationPriceCredits = parseRectificationPriceCredits(
      process.env.RECTIFICATION_PRICE_CREDITS,
    );
    const { data: profile, error } = await supabase
      .from("profiles")
      .select("credits,active_birth_time,birth_time_status")
      .eq("id", userId)
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
    const userId = user.id;

    const parsedPayload = accountProfilePatchSchema.safeParse(
      await request.json().catch(() => null),
    );
    if (!parsedPayload.success) return NextResponse.json({
      error: "账户资料格式不正确",
      details: parsedPayload.error.flatten(),
    }, { status: 400 });
    const payload = parsedPayload.data;

    const admin = createAdminSupabaseClient();
    let { data: currentProfile, error: currentProfileError } = await admin
      .from("profiles")
      .select("birth_date,birth_time,reported_birth_time,active_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,birth_time_status,rectification_case_id,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset")
      .eq("id", userId)
      .maybeSingle();
    if (currentProfileError && isMissingProfileColumn(currentProfileError)) {
      const fallback = await admin
        .from("profiles")
        .select("birth_date,birth_time,reported_birth_time,active_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,birth_time_status,rectification_case_id,country_code,province_code,city_code,district_code")
        .eq("id", userId)
        .maybeSingle();
      currentProfile = fallback.data ? {
        ...fallback.data,
        latitude: undefined,
        longitude: undefined,
        timezone_offset: undefined,
      } : null;
      currentProfileError = fallback.error;
    }
    if (currentProfileError) {
      return NextResponse.json({ error: "暂时无法核对现有出生资料" }, { status: 500 });
    }
    const applicationPatch = currentProfile
      ? resolveAccountBirthTimeApplicationPatch(currentProfile, payload)
      : {};
    const baseProfile = {
      id: userId,
      ...(payload.name !== undefined ? { name: payload.name } : {}),
      ...(payload.birth_date !== undefined ? { birth_date: payload.birth_date } : {}),
      ...(payload.reported_birth_time !== undefined
        ? { reported_birth_time: payload.reported_birth_time }
        : {}),
      ...(payload.birth_time_source !== undefined
        ? { birth_time_source: payload.birth_time_source }
        : {}),
      ...(payload.birth_time_period !== undefined
        ? { birth_time_period: payload.birth_time_period }
        : {}),
      ...(payload.birth_time_clue !== undefined
        ? { birth_time_clue: payload.birth_time_clue }
        : {}),
      ...(payload.uncertainty_before_minutes !== undefined
        ? { uncertainty_before_minutes: payload.uncertainty_before_minutes }
        : {}),
      ...(payload.uncertainty_after_minutes !== undefined
        ? { uncertainty_after_minutes: payload.uncertainty_after_minutes }
        : {}),
      ...(payload.country_code !== undefined ? { country_code: payload.country_code } : {}),
      ...(payload.province_code !== undefined ? { province_code: payload.province_code } : {}),
      ...(payload.city_code !== undefined ? { city_code: payload.city_code } : {}),
      ...(payload.district_code !== undefined ? { district_code: payload.district_code } : {}),
      ...applicationPatch,
      updated_at: new Date().toISOString(),
    };
    const withCoordinates = {
      ...baseProfile,
      ...(payload.latitude !== undefined ? { latitude: payload.latitude } : {}),
      ...(payload.longitude !== undefined ? { longitude: payload.longitude } : {}),
      ...(payload.timezone_offset !== undefined ? { timezone_offset: payload.timezone_offset } : {}),
    };
    const withoutCoordinates = baseProfile;
    const invalidatesUnconfirmedApplication = Object.keys(applicationPatch).length > 0;
    async function writeProfile(values: Record<string, unknown>) {
      if (!currentProfile) {
        return admin
          .from("profiles")
          .upsert(values, { onConflict: "id" })
          .select("id")
          .maybeSingle();
      }
      let query = admin.from("profiles").update(values).eq("id", userId);
      if (invalidatesUnconfirmedApplication) {
        query = applyAccountProfileConcurrencyGuards(query, currentProfile);
      }
      return query.select("id").maybeSingle();
    }

    let { data, error } = await writeProfile(withCoordinates);
    if (error && isMissingProfileColumn(error)) {
      const fallback = await writeProfile(withoutCoordinates);
      data = fallback.data;
      error = fallback.error;
    }

    if (!error && !data && invalidatesUnconfirmedApplication) {
      return NextResponse.json({
        error: "出生时间状态已经变化",
        message: "最新确认结果已保留，请刷新后重新编辑。",
      }, { status: 409 });
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
