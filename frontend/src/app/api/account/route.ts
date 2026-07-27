import { NextResponse } from "next/server";
import {
  parseRectificationPriceCredits,
} from "@/lib/birth-time-consultation-consent";
import { resolveAccountRectificationCase, resolveAccountRectificationV4Case } from "@/lib/account-rectification-case";
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

const unfinishedRectificationStatuses = ["starting", "active", "paused", "confirming"] as const;

function isMissingProfileColumn(error: { code?: string; message?: string } | null) {
  const message = error?.message?.toLowerCase() ?? "";
  return error?.code === "PGRST204"
    || error?.code === "42703"
    || message.includes("schema cache")
    || message.includes("column");
}

function isMissingRectificationV4Relation(error: { code?: string; message?: string } | null) {
  const message = error?.message?.toLowerCase() ?? "";
  return error?.code === "42P01"
    || error?.code === "PGRST205"
    || message.includes('relation "public.birth_time_rectification_v4_cases" does not exist')
    || (message.includes("schema cache") && message.includes("birth_time_rectification_v4_cases"));
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
    const admin = createAdminSupabaseClient();
    const { data: rectificationV4CaseData, error: rectificationV4CaseError } = await admin
      .from("birth_time_rectification_v4_cases")
      .select("id,status,version,accepted_range_start,updated_at")
      .eq("user_id", user.id)
      .neq("status", "abandoned")
      .is("accepted_range_start", null)
      .order("updated_at", { ascending: false })
      .limit(1);
    if (rectificationV4CaseError && !isMissingRectificationV4Relation(rectificationV4CaseError)) {
      return NextResponse.json({ error: "暂时无法读取生时校正状态" }, { status: 500 });
    }
    const rectificationV4CaseRows = rectificationV4CaseError ? [] : rectificationV4CaseData;

    const { data: rectificationCaseRows, error: rectificationCaseError } = await admin
      .from("birth_time_rectification_cases")
      .select("id,journey_protocol,status,turn_version,revision_of_case_id,baseline_active_time,declared_birth_input,updated_at")
      .eq("user_id", user.id)
      .eq("journey_protocol", "conversational-evidence-v3")
      .in("status", [...unfinishedRectificationStatuses])
      .order("updated_at", { ascending: false })
      .limit(50);
    if (rectificationCaseError) {
      return NextResponse.json({ error: "暂时无法读取生时校正状态" }, { status: 500 });
    }

    // Read the profile after the case snapshot. If a declaration edit races
    // with this request, matching uses the later profile and cannot resurrect
    // an older case. A concurrently created case simply appears on refresh.
    let { data: profile, error: profileError } = await supabase
      .from("profiles")
      .select("credits,active_birth_time,birth_time_status,birth_date,reported_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset,birth_place_label,birth_place_type,birth_place_provider,birth_place_provider_id,timezone_id,timezone_source")
      .eq("id", userId)
      .single();

    if (profileError && isMissingProfileColumn(profileError)) {
      const fallback = await supabase
        .from("profiles")
        .select("credits,active_birth_time,birth_time_status,birth_date,reported_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset")
        .eq("id", userId)
        .single();
      profile = fallback.data ? {
        ...fallback.data,
        birth_place_label: undefined,
        birth_place_type: undefined,
        birth_place_provider: undefined,
        birth_place_provider_id: undefined,
        timezone_id: undefined,
        timezone_source: undefined,
      } : null;
      profileError = fallback.error;
    }

    if (profileError || !profile) {
      return NextResponse.json({ error: "暂时无法读取账户余额" }, { status: 500 });
    }
    const rectificationCase = resolveAccountRectificationV4Case(
      Array.isArray(rectificationV4CaseRows) ? rectificationV4CaseRows : [],
    ) ?? resolveAccountRectificationCase(
      profile,
      Array.isArray(rectificationCaseRows) ? rectificationCaseRows : [],
    );

    return NextResponse.json({
      user: { id: user.id, email: user.email ?? null },
      credits: profile.credits,
      isAdmin: isAdminEmail(user.email),
      rectificationPriceCredits,
      hasConfirmedBirthTime: profile.birth_time_status === "confirmed"
        && typeof profile.active_birth_time === "string",
      rectificationCase,
      birthLocation: {
        label: profile.birth_place_label ?? null,
        placeType: profile.birth_place_type ?? null,
        provider: profile.birth_place_provider ?? null,
        providerPlaceId: profile.birth_place_provider_id ?? null,
        timezoneId: profile.timezone_id ?? null,
        timezoneSource: profile.timezone_source ?? null,
        timezoneOffset: profile.timezone_offset ?? null,
        latitude: profile.latitude ?? null,
        longitude: profile.longitude ?? null,
      },
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
      .select("birth_date,birth_time,reported_birth_time,active_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,birth_time_status,rectification_case_id,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset,birth_place_label,birth_place_type,birth_place_provider,birth_place_provider_id,timezone_id,timezone_source")
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
        birth_place_label: undefined,
        birth_place_type: undefined,
        birth_place_provider: undefined,
        birth_place_provider_id: undefined,
        timezone_id: undefined,
        timezone_source: undefined,
      } : null;
      currentProfileError = fallback.error;
    }
    if (currentProfileError) {
      return NextResponse.json({ error: "暂时无法核对现有出生资料" }, { status: 500 });
    }
    const applicationPatch = resolveAccountBirthTimeApplicationPatch(currentProfile, payload);
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
      ...(payload.birth_place_label !== undefined ? { birth_place_label: payload.birth_place_label } : {}),
      ...(payload.birth_place_type !== undefined ? { birth_place_type: payload.birth_place_type } : {}),
      ...(payload.birth_place_provider !== undefined ? { birth_place_provider: payload.birth_place_provider } : {}),
      ...(payload.birth_place_provider_id !== undefined ? { birth_place_provider_id: payload.birth_place_provider_id } : {}),
      ...(payload.timezone_id !== undefined ? { timezone_id: payload.timezone_id } : {}),
      ...(payload.timezone_source !== undefined ? { timezone_source: payload.timezone_source } : {}),
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
