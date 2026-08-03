import type { SupabaseClient } from "@supabase/supabase-js";
import type { AgenticRectificationContext } from "@/mastra/rectification-tools";
import { parseBirthDate } from "../birth-time-intake-model.ts";

/**
 * Agentic rectification session support.
 *
 * The server owns everything the LLM is not allowed to decide: the user's
 * birth profile, the baseline active birth time, and the only write path to
 * `profiles.active_birth_time`. The LLM can never persist an arbitrary minute;
 * the save tool re-validates against the engine's confirmation gate in the
 * same session and only then calls this module's RPC-backed writer.
 */

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
  baselineActiveTime: string | null;
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
  const before = uncertaintyBefore ?? 0;
  const after = uncertaintyAfter ?? 0;
  const total = Math.max(before, after);
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

  const persistedBirthDate = typeof data.birth_date === "string" ? data.birth_date.trim() : "";
  const birthDate = persistedBirthDate.slice(0, 10);
  if (!parseBirthDate(birthDate)
    || (persistedBirthDate.length > 10 && persistedBirthDate[10] !== "T")) {
    throw new AgenticRectificationProfileError("missing_birth_date");
  }
  const activeTime = timeValue(data.active_birth_time);
  const reportedTime = timeValue(data.reported_birth_time);
  const lat = numberOrNull(data.latitude);
  const lon = numberOrNull(data.longitude);
  const tz = numberOrNull(data.timezone_offset);
  if (lat === null || lon === null || tz === null) {
    throw new AgenticRectificationProfileError("missing_birth_place");
  }
  const timeSource = timeSourceFrom(data.birth_time_source);
  const uncertaintyBefore = numberOrNull(data.uncertainty_before_minutes);
  const uncertaintyAfter = numberOrNull(data.uncertainty_after_minutes);
  const candidateRange = candidateRangeFrom({
    activeTime,
    reportedTime,
    source: typeof data.birth_time_source === "string" ? data.birth_time_source.trim() : "",
    period: data.birth_time_period,
    uncertaintyBefore,
    uncertaintyAfter,
  });

  return {
    birth_date: birthDate,
    reported_time: activeTime ?? reportedTime,
    candidateRange,
    lat,
    lon,
    tz,
    declaredAccuracy: declaredAccuracyFrom(uncertaintyBefore, uncertaintyAfter, data.birth_time_source),
    timeSource,
    baselineActiveTime: activeTime,
  };
}

export function createAgenticRectificationContext(
  accounting: AccountingClient,
  userId: string,
  profile: AgenticRectificationProfile,
): AgenticRectificationContext {
  return {
    userId,
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
    async applyConfirmedBirthTime(time) {
      if (!/^\d{2}:\d{2}$/.test(time)) {
        return { ok: false, reason: "invalid_time_format" };
      }
      try {
        const { data, error } = await accounting.rpc("apply_agentic_rectification_birth_time", {
          p_user_id: userId,
          p_time: time,
          p_baseline_time: profile.baselineActiveTime,
          p_source: "agentic-rectification",
        });
        if (error) return { ok: false, reason: error.message };
        const candidate = Array.isArray(data) ? data[0] : data;
        if (candidate && typeof candidate === "object"
          && (candidate as { success?: boolean }).success === true) {
          return { ok: true, saved_time: String((candidate as { saved_time?: unknown }).saved_time ?? time) };
        }
        const reason = candidate && typeof candidate === "object"
          ? String((candidate as { error?: unknown }).error ?? "rpc_rejected")
          : "rpc_rejected";
        return { ok: false, reason };
      } catch (error) {
        return { ok: false, reason: error instanceof Error ? error.message : "rpc_failed" };
      }
    },
  };
}
