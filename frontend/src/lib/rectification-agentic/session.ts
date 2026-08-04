import type { SupabaseClient } from "@supabase/supabase-js";
import type {
  AgenticRectificationCandidate,
  AgenticRectificationCandidateResult,
  AgenticRectificationContext,
} from "@/mastra/rectification-tools";
import { normalizePersistedBirthDate } from "../birth-time-intake-model.ts";

type AccountingClient = SupabaseClient;

export class AgenticRectificationProfileError extends Error {
  readonly code: string;

  constructor(code: string) {
    super(`Agentic rectification profile error: ${code}`);
    this.name = "AgenticRectificationProfileError";
    this.code = code;
  }
}

export type AgenticRectificationProfile = Readonly<{
  birth_date: string;
  reported_time: string | null;
  candidateRange: AgenticRectificationContext["candidateRange"];
  lat: number;
  lon: number;
  tz: number;
  declaredAccuracy: AgenticRectificationContext["declaredAccuracy"];
  timeSource: AgenticRectificationContext["timeSource"];
  baselineReportedTime: string | null;
  baselineActiveTime: string | null;
  baselineBirthTimeSource: string | null;
  baselineBirthTimePeriod: string | null;
  baselineUncertaintyBeforeMinutes: number | null;
  baselineUncertaintyAfterMinutes: number | null;
}>;

export type StoredAgenticRectificationResult = Readonly<{
  resultId: string;
  candidates: readonly AgenticRectificationCandidate[];
  overallConfidence: "low" | "medium" | "high";
  marginPercent: number | null;
  selectionAllowed: boolean;
  confirmationAllowed: boolean;
  representativeTime: string | null;
  selectedTime: string | null;
  selectionStatus: "accepted" | "confirmed" | null;
}>;

const timeValue = (value: unknown): string | null => {
  const time = typeof value === "string" ? value.slice(0, 5) : "";
  return /^([01]\d|2[0-3]):[0-5]\d$/.test(time) ? time : null;
};

const periodRanges = {
  early_morning: { start_time: "04:00", end_time: "07:59" },
  morning: { start_time: "08:00", end_time: "11:59" },
  afternoon: { start_time: "12:00", end_time: "17:59" },
  evening: { start_time: "18:00", end_time: "22:59" },
  late_night: { start_time: "23:00", end_time: "03:59" },
} as const;

function shiftedTime(time: string, offsetMinutes: number): string {
  const [hour = 0, minute = 0] = time.split(":").map(Number);
  const normalized = ((hour * 60 + minute + offsetMinutes) % 1_440 + 1_440) % 1_440;
  return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
}

function candidateRangeFrom(input: {
  activeTime: string | null;
  reportedTime: string | null;
  source: string;
  period: unknown;
  uncertaintyBefore: number | null;
  uncertaintyAfter: number | null;
}): AgenticRectificationContext["candidateRange"] {
  const referenceTime = input.activeTime ?? input.reportedTime;
  if (referenceTime) {
    const fallback = input.source === "hospital_record" || input.source === "hospital"
      ? 2
      : input.source === "family_exact" || input.source === "family_clear"
        ? 15
        : input.source === "approximate" || input.source === "family_vague"
          ? 60
          : 2;
    return {
      start_time: shiftedTime(referenceTime, -(input.uncertaintyBefore ?? fallback)),
      end_time: shiftedTime(referenceTime, input.uncertaintyAfter ?? fallback),
    };
  }
  if (input.source === "period_only" || input.source === "legacy_import") {
    const period = typeof input.period === "string"
      ? periodRanges[input.period as keyof typeof periodRanges]
      : null;
    if (period) return period;
    if (input.source === "period_only") throw new AgenticRectificationProfileError("missing_birth_time_period");
  }
  if (input.source === "unknown" || input.source === "legacy_import") {
    return { start_time: "00:00", end_time: "23:59" };
  }
  throw new AgenticRectificationProfileError("missing_birth_time");
}

function declaredAccuracyFrom(uncertaintyBefore: number | null, uncertaintyAfter: number | null, timeSource: string | null): AgenticRectificationContext["declaredAccuracy"] {
  const total = Math.max(uncertaintyBefore ?? 0, uncertaintyAfter ?? 0);
  if (total > 0) {
    if (total <= 5) return "minute";
    if (total <= 15) return "15min";
    if (total <= 60) return "1hour";
    return "unknown";
  }
  switch (timeSource) {
    case "hospital":
    case "hospital_record": return "minute";
    case "family_clear":
    case "family_exact": return "15min";
    case "family_vague":
    case "approximate": return "1hour";
    default: return "unknown";
  }
}

function timeSourceFrom(value: unknown): AgenticRectificationContext["timeSource"] {
  const source = typeof value === "string" ? value.trim() : "";
  if (source === "hospital" || source === "hospital_record") return "hospital";
  if (source === "family_clear" || source === "family_exact") return "family_clear";
  if (source === "family_vague" || source === "approximate" || source === "period_only") return "family_vague";
  return "unknown";
}

function numberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function readCandidates(value: unknown): AgenticRectificationCandidate[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((candidate): AgenticRectificationCandidate[] => {
    if (!candidate || typeof candidate !== "object") return [];
    const row = candidate as Record<string, unknown>;
    const time = timeValue(row.time);
    if (!time || typeof row.rank !== "number" || typeof row.relative_support !== "number") return [];
    return [{
      rank: Math.trunc(row.rank),
      time,
      relative_support: Math.max(0, Math.min(100, Math.trunc(row.relative_support))),
      tied_minute_count: typeof row.tied_minute_count === "number" ? Math.max(1, Math.trunc(row.tied_minute_count)) : 1,
    }];
  });
}

function publicResult(value: unknown): StoredAgenticRectificationResult | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  const resultId = typeof row.id === "string" ? row.id : "";
  if (!resultId) return null;
  const selectionKind = row.selection_kind;
  return {
    resultId,
    candidates: readCandidates(row.candidates),
    overallConfidence: row.overall_confidence === "high" || row.overall_confidence === "medium" ? row.overall_confidence : "low",
    marginPercent: numberOrNull(row.margin_percent),
    selectionAllowed: row.selection_allowed === true,
    confirmationAllowed: row.confirmation_allowed === true,
    representativeTime: timeValue(row.representative_time),
    selectedTime: timeValue(row.selected_time),
    selectionStatus: selectionKind === "engine_confirmed" ? "confirmed" : selectionKind === "user_accepted" ? "accepted" : null,
  };
}

export async function loadAgenticRectificationProfile(
  accounting: AccountingClient,
  userId: string,
): Promise<AgenticRectificationProfile> {
  const { data, error } = await accounting
    .from("profiles")
    .select("birth_date,reported_birth_time,active_birth_time,birth_time_source,birth_time_period,uncertainty_before_minutes,uncertainty_after_minutes,latitude,longitude,timezone_offset")
    .eq("id", userId)
    .single();
  if (error || !data) throw new AgenticRectificationProfileError("profile_unavailable");

  const birthDate = normalizePersistedBirthDate(data.birth_date);
  if (!birthDate) throw new AgenticRectificationProfileError("missing_birth_date");
  const activeTime = timeValue(data.active_birth_time);
  const reportedTime = timeValue(data.reported_birth_time);
  const lat = numberOrNull(data.latitude);
  const lon = numberOrNull(data.longitude);
  const tz = numberOrNull(data.timezone_offset);
  if (lat === null || lon === null || tz === null) throw new AgenticRectificationProfileError("missing_birth_place");

  const rawSource = typeof data.birth_time_source === "string" ? data.birth_time_source.trim() : "";
  const uncertaintyBefore = numberOrNull(data.uncertainty_before_minutes);
  const uncertaintyAfter = numberOrNull(data.uncertainty_after_minutes);
  return {
    birth_date: birthDate,
    reported_time: activeTime ?? reportedTime,
    candidateRange: candidateRangeFrom({
      activeTime,
      reportedTime,
      source: rawSource,
      period: data.birth_time_period,
      uncertaintyBefore,
      uncertaintyAfter,
    }),
    lat,
    lon,
    tz,
    declaredAccuracy: declaredAccuracyFrom(uncertaintyBefore, uncertaintyAfter, rawSource),
    timeSource: timeSourceFrom(rawSource),
    baselineReportedTime: reportedTime,
    baselineActiveTime: activeTime,
    baselineBirthTimeSource: rawSource || null,
    baselineBirthTimePeriod: typeof data.birth_time_period === "string" ? data.birth_time_period : null,
    baselineUncertaintyBeforeMinutes: uncertaintyBefore,
    baselineUncertaintyAfterMinutes: uncertaintyAfter,
  };
}

export async function loadLatestAgenticRectificationResult(
  accounting: AccountingClient,
  userId: string,
  sessionId: string,
): Promise<StoredAgenticRectificationResult | null> {
  const { data, error } = await accounting
    .from("agentic_rectification_results")
    .select("id,candidates,overall_confidence,margin_percent,selection_allowed,confirmation_allowed,representative_time,selected_time,selection_kind")
    .eq("user_id", userId)
    .eq("session_id", sessionId)
    .is("invalidated_at", null)
    .gt("expires_at", new Date().toISOString())
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw new Error("AgenticRectificationResultReadError");
  return publicResult(data);
}

export async function acceptAgenticRectificationCandidate(
  accounting: AccountingClient,
  userId: string,
  sessionId: string,
  time: string,
  resultId?: string,
): Promise<Awaited<ReturnType<AgenticRectificationContext["acceptCandidate"]>>> {
  if (!timeValue(time) || time.length !== 5) return { ok: false, reason: "invalid_time_format" };
  let resolvedResultId = resultId;
  if (!resolvedResultId) {
    try {
      resolvedResultId = (await loadLatestAgenticRectificationResult(accounting, userId, sessionId))?.resultId;
    } catch {
      return { ok: false, reason: "candidate_result_unavailable" };
    }
  }
  if (!resolvedResultId) return { ok: false, reason: "candidate_result_not_found" };
  try {
    const { data, error } = await accounting.rpc("accept_agentic_rectification_candidate", {
      p_user_id: userId,
      p_session_id: sessionId,
      p_result_id: resolvedResultId,
      p_time: time,
    });
    if (error) return { ok: false, reason: error.message };
    const row = Array.isArray(data) ? data[0] : data;
    if (!row || typeof row !== "object" || (row as { success?: unknown }).success !== true) {
      return { ok: false, reason: "rpc_rejected" };
    }
    const result = row as Record<string, unknown>;
    const status = result.status === "confirmed" ? "confirmed" : result.status === "accepted" ? "accepted" : null;
    const savedTime = timeValue(result.saved_time);
    const savedResultId = typeof result.result_id === "string" ? result.result_id : resolvedResultId;
    if (!status || !savedTime) return { ok: false, reason: "rpc_invalid_response" };
    return { ok: true, saved_time: savedTime, status, result_id: savedResultId };
  } catch (error) {
    return { ok: false, reason: error instanceof Error ? error.message : "rpc_failed" };
  }
}

export function createAgenticRectificationContext(
  accounting: AccountingClient,
  userId: string,
  profile: AgenticRectificationProfile,
  sessionId: string,
): AgenticRectificationContext {
  return {
    userId,
    sessionId,
    birth: {
      birth_date: profile.birth_date,
      reported_time: profile.reported_time,
      lat: profile.lat,
      lon: profile.lon,
      tz: profile.tz,
    },
    candidateRange: profile.candidateRange,
    declaredAccuracy: profile.declaredAccuracy,
    timeSource: profile.timeSource,
    async persistCandidateResult(result: AgenticRectificationCandidateResult) {
      if (!result.engineResultId || !result.canonicalInputHash || result.candidates.length === 0) {
        return { ok: false, reason: "candidate_result_invalid" };
      }
      const { data, error } = await accounting
        .from("agentic_rectification_results")
        .upsert({
          user_id: userId,
          session_id: sessionId,
          engine_result_id: result.engineResultId,
          canonical_input_hash: result.canonicalInputHash,
          algorithm_version: result.algorithmVersion,
          candidate_range: result.candidateRange,
          candidates: result.candidates,
          overall_confidence: result.overallConfidence,
          margin_percent: result.marginPercent,
          selection_allowed: result.selectionAllowed,
          confirmation_allowed: result.confirmationAllowed,
          representative_time: result.representativeTime,
          baseline_birth_date: profile.birth_date,
          baseline_reported_birth_time: profile.baselineReportedTime,
          baseline_active_birth_time: profile.baselineActiveTime,
          baseline_birth_time_source: profile.baselineBirthTimeSource,
          baseline_birth_time_period: profile.baselineBirthTimePeriod,
          baseline_uncertainty_before_minutes: profile.baselineUncertaintyBeforeMinutes,
          baseline_uncertainty_after_minutes: profile.baselineUncertaintyAfterMinutes,
          baseline_latitude: profile.lat,
          baseline_longitude: profile.lon,
          baseline_timezone_offset: profile.tz,
        }, { onConflict: "user_id,session_id,engine_result_id" })
        .select("id")
        .single();
      if (error || !data || typeof data.id !== "string") return { ok: false, reason: error?.message ?? "candidate_result_write_failed" };
      return { ok: true, result_id: data.id };
    },
    acceptCandidate: (time, resultId) => acceptAgenticRectificationCandidate(accounting, userId, sessionId, time, resultId),
    async applyConfirmedBirthTime(time) {
      if (!timeValue(time) || time.length !== 5) return { ok: false, reason: "invalid_time_format" };
      try {
        const { data, error } = await accounting.rpc("apply_agentic_rectification_birth_time", {
          p_user_id: userId,
          p_time: time,
          p_baseline_time: profile.baselineActiveTime,
          p_source: "agentic-rectification",
        });
        if (error) return { ok: false, reason: error.message };
        const candidate = Array.isArray(data) ? data[0] : data;
        if (candidate && typeof candidate === "object" && (candidate as { success?: boolean }).success === true) {
          return { ok: true, saved_time: String((candidate as { saved_time?: unknown }).saved_time ?? time) };
        }
        return { ok: false, reason: candidate && typeof candidate === "object" ? String((candidate as { error?: unknown }).error ?? "rpc_rejected") : "rpc_rejected" };
      } catch (error) {
        return { ok: false, reason: error instanceof Error ? error.message : "rpc_failed" };
      }
    },
  };
}
