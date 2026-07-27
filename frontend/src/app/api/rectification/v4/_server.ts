import { NextResponse } from "next/server";
import { z } from "zod";
import { parseBirthTimeProfile } from "@/lib/birth-time-journey-adapters";
import { assessBirthTime } from "@/lib/birth-time-journey";
import { resolveMissingBirthTimezoneOffset } from "@/lib/birth-profile-timezone";
import type { CalculationSpec } from "@/lib/rectification-v4/contracts";
import { createRectificationV4CaseService } from "@/lib/rectification-v4/case-service";
import { RectificationV4StoreError } from "@/lib/rectification-v4/store";
import { createRectificationV4SupabaseStore } from "@/lib/rectification-v4/supabase-store";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

const idSchema = z.string().uuid();

export async function rectificationV4Context() {
  const auth = await createServerSupabaseClient();
  const { data: { user }, error } = await auth.auth.getUser();
  if (error || !user) throw new RectificationV4HttpError(401, "请先登录后再继续生时校正。");
  const admin = createAdminSupabaseClient();
  return {
    userId: user.id,
    auth,
    service: createRectificationV4CaseService(createRectificationV4SupabaseStore(admin)),
  };
}

export async function requestBody<T>(request: Request, schema: z.ZodType<T>): Promise<T> {
  const body = await request.json().catch(() => null);
  const parsed = schema.safeParse(body);
  if (!parsed.success) throw new RectificationV4HttpError(400, "提交内容不完整，请检查后重试。");
  return parsed.data;
}

export function routeId(value: string): string {
  const parsed = idSchema.safeParse(value);
  if (!parsed.success) throw new RectificationV4HttpError(404, "没有找到这次生时校正记录。");
  return parsed.data;
}

export async function calculationSpecForUser(
  auth: Awaited<ReturnType<typeof createServerSupabaseClient>>,
  userId: string,
): Promise<CalculationSpec> {
  const { data, error } = await auth.from("profiles")
    .select("birth_date,reported_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,latitude,longitude,timezone_id,timezone_offset")
    .eq("id", userId).maybeSingle();
  if (error) throw error;
  if (!data) throw new RectificationV4HttpError(409, "请先补全出生日期、时间线索和出生地点。");
  const profile = await resolveMissingBirthTimezoneOffset(data);
  const assessment = parseBirthTimeProfile(profile);
  const range = assessBirthTime(assessment, { kind: "unavailable" }).reportedRange;
  return {
    version: "rectification-calculation-spec-v4",
    birthDate: assessment.date,
    candidateRange: {
      start: range.startTime ?? "00:00",
      end: range.endTime ?? "23:59",
    },
    latitude: assessment.location.lat,
    longitude: assessment.location.lon,
    timezoneOffsetHours: assessment.location.tz,
    ayanamsa: "lahiri",
    nodeMode: "mean",
    minuteStep: 1,
  };
}

export class RectificationV4HttpError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
}

export function rectificationV4Error(error: unknown): NextResponse {
  if (error instanceof RectificationV4HttpError) {
    return NextResponse.json({ error: error.message }, { status: error.status });
  }
  if (error instanceof RectificationV4StoreError) {
    const responses: Record<RectificationV4StoreError["code"], readonly [number, string]> = {
      not_found: [404, "没有找到这次生时校正记录。"],
      stale_version: [409, "记录已在其他位置更新，正在重新载入。"],
      invalid_state: [409, "当前状态无法执行这个操作，请刷新后重试。"],
      stale_job: [409, "这次计算已过期，请以最新结果为准。"],
      lease_lost: [409, "计算任务已由其他进程接管，请稍后刷新。"],
    };
    const response = responses[error.code];
    return NextResponse.json({ error: response[1] }, { status: response[0] });
  }
  if (error instanceof z.ZodError) {
    return NextResponse.json({ error: "出生资料或提交内容格式不正确。" }, { status: 400 });
  }
  if (isSupabaseConfigurationError(error)) {
    return NextResponse.json({ error: "生时校正服务尚未配置。" }, { status: 503 });
  }
  console.error("rectification_v4_route_failed", error);
  return NextResponse.json({ error: "暂时无法处理，请稍后再试。" }, { status: 500 });
}
