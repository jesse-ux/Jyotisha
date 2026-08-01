import type { SupabaseClient } from "@supabase/supabase-js";
import type { AgenticRectificationContext } from "@/mastra/rectification-tools";

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
  reported_time: string;
  lat: number;
  lon: number;
  tz: number;
  declaredAccuracy: AgenticRectificationContext["declaredAccuracy"];
  timeSource: AgenticRectificationContext["timeSource"];
  baselineActiveTime: string | null;
}>;

const timeValue = (value: unknown): string | null => {
  if (typeof value !== "string" || !value) return null;
  return value.length >= 5 ? value.slice(0, 5) : null;
};

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
    case "hospital": return "minute";
    case "family_clear": return "15min";
    case "family_vague": return "1hour";
    default: return "unknown";
  }
}

function timeSourceFrom(value: unknown): AgenticRectificationContext["timeSource"] {
  const source = typeof value === "string" ? value.trim() : "";
  if (source === "hospital" || source === "family_clear" || source === "family_vague") return source;
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

  const birthDate = typeof data.birth_date === "string" ? data.birth_date.trim() : "";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(birthDate)) {
    throw new AgenticRectificationProfileError("missing_birth_date");
  }
  const reportedTime = timeValue(data.active_birth_time ?? data.reported_birth_time);
  if (!reportedTime || !/^\d{2}:\d{2}$/.test(reportedTime)) {
    throw new AgenticRectificationProfileError("missing_birth_time");
  }
  const lat = numberOrNull(data.latitude);
  const lon = numberOrNull(data.longitude);
  const tz = numberOrNull(data.timezone_offset);
  if (lat === null || lon === null || tz === null) {
    throw new AgenticRectificationProfileError("missing_birth_place");
  }
  const timeSource = timeSourceFrom(data.birth_time_source);
  const uncertaintyBefore = numberOrNull(data.uncertainty_before_minutes);
  const uncertaintyAfter = numberOrNull(data.uncertainty_after_minutes);

  return {
    birth_date: birthDate,
    reported_time: reportedTime,
    lat,
    lon,
    tz,
    declaredAccuracy: declaredAccuracyFrom(uncertaintyBefore, uncertaintyAfter, data.birth_time_source),
    timeSource,
    baselineActiveTime: timeValue(data.active_birth_time),
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
