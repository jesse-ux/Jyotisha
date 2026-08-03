import { createTool } from "@mastra/core/tools";
import { createHash } from "node:crypto";
import { z } from "zod";

/**
 * Agentic birth-time rectification tool layer.
 *
 * These tools let an LLM agent drive the full local Jyotish rectification
 * methodology the same way Claude Code drives `scripts/` locally: the agent
 * requests engine computations on demand instead of inventing results. Every
 * tool wraps one Python-engine HTTP endpoint (or a server-owned write).
 *
 * Hard boundary: the agent never writes a birth minute directly. The
 * `rectification-save-birth-time` tool only applies a minute that the engine's
 * high-rigor confirmation gate already produced in the same session, so the
 * LLM can never persist an arbitrary or invented time.
 */

const engineBase = process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200";

const timePattern = /^\d{2}:\d{2}$/;

/** Birth fields supplied by the server from the user profile (never by the LLM). */
export type AgenticRectificationBirth = Readonly<{
  birth_date: string;
  reported_time: string | null;
  lat: number;
  lon: number;
  tz: number;
}>;

export type AgenticRectificationCandidateRange = Readonly<{
  start_time: string;
  end_time: string;
}>;

export type AgenticRectificationContext = Readonly<{
  userId: string;
  engineBase?: string;
  birth: AgenticRectificationBirth;
  candidateRange: AgenticRectificationCandidateRange;
  declaredAccuracy?: "minute" | "15min" | "1hour" | "unknown";
  timeSource?: "hospital" | "family_clear" | "family_vague" | "unknown";
  applyConfirmedBirthTime: (time: string) => Promise<Readonly<{
    ok: true;
    saved_time: string;
  } | { ok: false; reason: string }>>;
}>;

export const rectificationDomainSchema = z.enum([
  "education", "relocation", "relationship", "career", "finance", "health_pressure",
]);
export type RectificationDomain = z.infer<typeof rectificationDomainSchema>;

/** One dated life event as the LLM supplies it (same shape for every tool). */
export const agenticRectificationEventSchema = z.object({
  id: z.string().min(1).max(64),
  domain: rectificationDomainSchema,
  date: z.string().min(4).max(23),
  precision: z.enum(["year", "month", "day", "range"]),
  summary: z.string().max(1000).optional(),
});
export type AgenticRectificationEvent = z.infer<typeof agenticRectificationEventSchema>;

export const candidateRangeSchema = z.object({
  start_time: z.string().regex(timePattern),
  end_time: z.string().regex(timePattern),
});

function clockMinute(value: string): number {
  const [hour = 0, minute = 0] = value.split(":").map(Number);
  return hour * 60 + minute;
}

function rangeScanWindow(range: AgenticRectificationCandidateRange) {
  const start = clockMinute(range.start_time);
  let end = clockMinute(range.end_time);
  if (end < start) end += 1_440;
  const width = end - start;
  const center = Math.round((start + end) / 2) % 1_440;
  return {
    width,
    centerTime: `${String(Math.floor(center / 60)).padStart(2, "0")}:${String(center % 60).padStart(2, "0")}`,
    uncertaintyMinutes: Math.max(1, Math.ceil(width / 2)),
  };
}

function requireServerCandidateRange(
  requested: AgenticRectificationCandidateRange,
  serverOwned: AgenticRectificationCandidateRange,
) {
  if (requested.start_time !== serverOwned.start_time || requested.end_time !== serverOwned.end_time) {
    throw new Error(`candidate_range_mismatch: use ${serverOwned.start_time}-${serverOwned.end_time}`);
  }
}

const defaultEventKind: Record<RectificationDomain, string> = {
  education: "education_milestone",
  relocation: "relocation",
  relationship: "relationship_change",
  career: "career_change",
  finance: "finance_change",
  health_pressure: "self_health_event",
};

/** Stable UUID derived from the agent-supplied event id so ids stay reusable. */
function stableEventId(rawId: string): string {
  const digest = createHash("sha256").update(`agentic-rectification:${rawId}`).digest();
  digest[6] = (digest[6]! & 0x0f) | 0x40;
  digest[8] = (digest[8]! & 0x3f) | 0x80;
  const hex = digest.toString("hex");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20, 32)}`;
}

/** Normalize the LLM's simple event into the V5 (`date_start`/`date_end`) shape. */
function toV5Event(event: AgenticRectificationEvent): Readonly<{
  id: string;
  domain: RectificationDomain;
  event_kind: string;
  date_start: string;
  date_end: string;
  precision: "day" | "month" | "quarter" | "year" | "range";
  summary?: string;
}> {
  const [startPart, endPart] = event.date.includes("..")
    ? event.date.split("..", 2)
    : [event.date, ""];
  const startDate = normalizeDateStart(startPart, event.precision);
  const endDate = endPart ? normalizeDateStart(endPart, event.precision) : normalizeDateEnd(startPart, event.precision);
  const normalizedPrecision = event.precision === "range" || endPart ? "range" : event.precision === "day" ? "day" : event.precision === "month" ? "month" : "year";
  return {
    id: stableEventId(event.id),
    domain: event.domain,
    event_kind: defaultEventKind[event.domain],
    date_start: startDate,
    date_end: endDate,
    precision: normalizedPrecision,
    summary: event.summary,
  };
}

function normalizeDateStart(date: string, precision: AgenticRectificationEvent["precision"]): string {
  const [year, month = "01", day = "01"] = date.split("-");
  const paddedMonth = month.length === 1 ? `0${month}` : month;
  const paddedDay = day.length === 1 ? `0${day}` : day;
  if (precision === "year" || !paddedMonth) return `${year}-01-01`;
  return `${year}-${paddedMonth}-${paddedDay}`;
}

function normalizeDateEnd(date: string, precision: AgenticRectificationEvent["precision"]): string {
  const [year, month, day] = date.split("-");
  if (precision === "year" || !month) return `${year}-12-31`;
  if (precision === "month" || !day) {
    const last = new Date(Number(year), Number(month), 0).getDate();
    return `${year}-${month.length === 1 ? `0${month}` : month}-${String(last).padStart(2, "0")}`;
  }
  return `${year}-${month.length === 1 ? `0${month}` : month}-${day.length === 1 ? `0${day}` : day}`;
}

/** Convert a V5 event to the v3 events schema used by `/api/active_rectification_events`. */
function toV3Event(event: AgenticRectificationEvent): Readonly<{
  id: string;
  domain: RectificationDomain;
  date: string;
  precision: "day" | "month" | "year";
  summary?: string;
}> {
  const v5 = toV5Event(event);
  const precision = v5.precision === "day" ? "day" : v5.precision === "month" ? "month" : "year";
  return { id: v5.id, domain: v5.domain, date: v5.date_start, precision, summary: v5.summary };
}

async function postEngine(base: string, path: string, body: unknown): Promise<Record<string, unknown>> {
  const response = await fetch(`${base}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(60_000),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.error || data?.message || `Jyotish API ${path} returned ${response.status}`;
    throw new Error(message);
  }
  if (!data || typeof data !== "object") throw new Error(`Jyotish API ${path} returned an invalid response`);
  return data as Record<string, unknown>;
}

function v5Request(
  ctx: AgenticRectificationContext,
  candidateRange: z.infer<typeof candidateRangeSchema>,
  events: readonly AgenticRectificationEvent[],
) {
  return {
    birth_date: ctx.birth.birth_date,
    start_time: candidateRange.start_time,
    end_time: candidateRange.end_time,
    lat: ctx.birth.lat,
    lon: ctx.birth.lon,
    tz: ctx.birth.tz,
    events: events.map(toV5Event),
  };
}

function topCandidates(value: unknown, limit = 6): unknown {
  const scores = Array.isArray(value)
    ? (value as Array<Record<string, unknown>>)
    : [];
  return scores.slice(0, limit);
}

function compactRobustness(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object") return null;
  const robustness = value as Record<string, unknown>;
  return {
    neighbor_support_minutes: robustness.neighbor_support_minutes,
    leave_one_out_retention_rate: robustness.leave_one_out_retention_rate,
    leave_one_domain_out_retention_rate: robustness.leave_one_domain_out_retention_rate,
    date_sensitivity_retention_rate: robustness.date_sensitivity_retention_rate,
  };
}

function compactScoreResult(data: Record<string, unknown>): Record<string, unknown> {
  const diagnostics = (data.diagnostics && typeof data.diagnostics === "object")
    ? data.diagnostics as Record<string, unknown>
    : {};
  return {
    endpoint: data.endpoint,
    result_id: data.result_id,
    algorithm_version: data.algorithm_version,
    calculation_spec_hash: data.calculation_spec_hash,
    candidate_count: Array.isArray(data.candidate_scores) ? (data.candidate_scores as unknown[]).length : 0,
    top_candidates: topCandidates(data.candidate_scores),
    robustness: compactRobustness(data.robustness),
    diagnostics_summary: {
      primary_cluster_retention_rate: diagnostics.primary_cluster_retention_rate,
      primary_secondary_margin_percent: diagnostics.primary_secondary_margin_percent,
      most_discriminating_layers: diagnostics.most_discriminating_layers,
      candidate_splits: diagnostics.candidate_splits,
      unstable_event_ids: diagnostics.unstable_event_ids,
    },
    missing_layers: data.missing_layers,
    can_confirm_exact_minute: data.can_confirm_exact_minute,
  };
}

export function createAgenticRectificationTools(ctx: AgenticRectificationContext) {
  const base = ctx.engineBase ?? engineBase;
  // Server-owned confirmation gate for this session: only a minute the engine
  // produced through the high-rigor gate may ever be persisted.
  let confirmedGate: Readonly<{ time: string; resultId: string }> | null = null;

  const gateTool = createTool({
    id: "rectification-gate",
    description:
      "Run the birth-time precision gate: computes effective accuracy, enabled divisional charts, lagna boundary sensitivity, and recommended dated-event types for the user's reported birth time. Call this first to understand the starting precision and which events are most valuable.",
    inputSchema: z.object({
      declared_accuracy: z.enum(["minute", "15min", "1hour", "unknown"]).optional(),
      time_source: z.enum(["hospital", "family_clear", "family_vague", "unknown"]).optional(),
    }).strict(),
    execute: async (input) => {
      if (!ctx.birth.reported_time) {
        return {
          endpoint: "server_owned_rectification_preflight",
          effective_accuracy: ctx.declaredAccuracy ?? "unknown",
          candidate_range: ctx.candidateRange,
          lagna_boundary: { is_sensitive: null, note: "requires_dated_event_scoring_across_candidate_range" },
          enabled_vargas: {},
          summary: {
            headline: "broad_candidate_range",
            enabled: [],
            warned: ["candidate_range_requires_event_scoring"],
            disabled: ["single_minute_precision_claims"],
            confidence_floor: "low",
            recommended_events: ["education", "career", "relationship", "relocation"],
            next_action: "collect one clearly dated life event",
          },
        };
      }
      const body = {
        year: Number(ctx.birth.birth_date.slice(0, 4)),
        month: Number(ctx.birth.birth_date.slice(5, 7)),
        day: Number(ctx.birth.birth_date.slice(8, 10)),
        hour: Number(ctx.birth.reported_time.slice(0, 2)),
        minute: Number(ctx.birth.reported_time.slice(3, 5)),
        lat: ctx.birth.lat,
        lon: ctx.birth.lon,
        tz: ctx.birth.tz,
        declared_accuracy: input.declared_accuracy ?? ctx.declaredAccuracy ?? "unknown",
        time_source: input.time_source ?? ctx.timeSource ?? "family_clear",
      };
      const data = await postEngine(base, "/api/rectification_gate", body);
      const summary = (data.summary && typeof data.summary === "object")
        ? data.summary as Record<string, unknown>
        : {};
      return {
        endpoint: data.endpoint,
        effective_accuracy: data.effective_accuracy,
        candidate_range: ctx.candidateRange,
        lagna_boundary: data.lagna_boundary,
        enabled_vargas: data.enabled_vargas,
        summary: {
          headline: summary.headline,
          enabled: summary.enabled,
          warned: summary.warned,
          disabled: summary.disabled,
          confidence_floor: summary.confidence_floor,
          recommended_events: summary.recommended_events,
          next_action: summary.next_action,
        },
      };
    },
  });

  const scanTool = createTool({
    id: "rectification-scan",
    description:
      "Scan how chart layers change minute-to-minute across the server-owned candidate range. Wide ranges are deferred until dated-event scoring narrows the evidence.",
    inputSchema: z.object({
      step_minutes: z.number().int().min(1).max(30).optional(),
    }).strict(),
    execute: async (input) => {
      const scanWindow = rangeScanWindow(ctx.candidateRange);
      if (scanWindow.width > 360) {
        return {
          scope: "candidate_time_sensitivity_scan",
          status: "deferred_wide_range",
          candidate_range: ctx.candidateRange,
          boundary: "Collect dated events and score the server-owned full range before running a local sensitivity scan.",
        };
      }
      const body = {
        year: Number(ctx.birth.birth_date.slice(0, 4)),
        month: Number(ctx.birth.birth_date.slice(5, 7)),
        day: Number(ctx.birth.birth_date.slice(8, 10)),
        hour: Number(scanWindow.centerTime.slice(0, 2)),
        minute: Number(scanWindow.centerTime.slice(3, 5)),
        lat: ctx.birth.lat,
        lon: ctx.birth.lon,
        tz: ctx.birth.tz,
        time_uncertainty_minutes: scanWindow.uncertaintyMinutes,
        step_minutes: input.step_minutes,
      };
      const data = await postEngine(base, "/api/rectification/sensitivity_scan", body);
      const rows = Array.isArray(data.rows) ? (data.rows as unknown[]) : [];
      return {
        scope: data.scope,
        status: data.status,
        candidate_range: ctx.candidateRange,
        center_time: data.center_time,
        uncertainty_minutes: data.uncertainty_minutes,
        step_minutes: data.step_minutes,
        candidate_count: data.candidate_count,
        sensitivity_summary: {
          sensitive_layers: rows.reduce<Record<string, number>>((acc, row) => {
            const sensitive = (row as Record<string, unknown>).sensitive_layers;
            if (Array.isArray(sensitive)) {
              for (const layer of sensitive as string[]) acc[layer] = (acc[layer] ?? 0) + 1;
            }
            return acc;
          }, {}),
          high_sensitivity_layers: Object.entries(
            rows.reduce<Record<string, number>>((acc, row) => {
              const sensitive = (row as Record<string, unknown>).sensitive_layers;
              if (Array.isArray(sensitive)) {
                for (const layer of sensitive as string[]) acc[layer] = (acc[layer] ?? 0) + 1;
              }
              return acc;
            }, {}),
          ).filter(([, count]) => count >= Math.max(1, rows.length / 4)).map(([layer]) => layer),
        },
        supported_vargas: data.supported_vargas,
        unavailable_vargas: data.unavailable_vargas,
        pending_layers: data.pending_layers,
        transitions: Array.isArray(data.transitions) ? (data.transitions as unknown[]).slice(0, 12) : [],
        boundary: data.boundary,
      };
    },
  });

  const scoreTool = createTool({
    id: "rectification-score",
    description:
      "Score candidate birth minutes against the user's dated life events using the V5 matrix engine (Vimshottari/Narayana/D2-D30/Arudha/Ashtakavarga/Shadbala). Returns the top candidate minutes, robustness, and missing layers. Supply dated events you have confirmed with the user. Keep event ids stable across calls.",
    inputSchema: z.object({
      candidate_range: candidateRangeSchema,
      events: z.array(agenticRectificationEventSchema).min(1).max(40),
    }).strict(),
    execute: async (input) => {
      requireServerCandidateRange(input.candidate_range, ctx.candidateRange);
      const data = await postEngine(base, "/api/rectification/v5/score", v5Request(ctx, input.candidate_range, input.events));
      return compactScoreResult(data);
    },
  });

  const diagnosticsTool = createTool({
    id: "rectification-diagnostics",
    description:
      "Run robustness diagnostics over the candidate range for the user's dated events: leave-one-event-out and leave-one-domain-out retention, date sensitivity, neighbor stability, candidate splits, and unstable events. Use this to decide which event to clarify next.",
    inputSchema: z.object({
      candidate_range: candidateRangeSchema,
      events: z.array(agenticRectificationEventSchema).min(1).max(40),
    }).strict(),
    execute: async (input) => {
      requireServerCandidateRange(input.candidate_range, ctx.candidateRange);
      const data = await postEngine(base, "/api/rectification/v5/diagnostics", v5Request(ctx, input.candidate_range, input.events));
      const diagnostics = (data.diagnostics && typeof data.diagnostics === "object")
        ? data.diagnostics as Record<string, unknown>
        : {};
      return {
        endpoint: data.endpoint,
        result_id: data.result_id,
        algorithm_version: data.algorithm_version,
        diagnostics: {
          primary_cluster_retention_rate: diagnostics.primary_cluster_retention_rate,
          leave_one_event_out_retention_rate: diagnostics.leave_one_event_out_retention_rate,
          leave_one_domain_out_retention_rate: diagnostics.leave_one_domain_out_retention_rate,
          date_sensitivity_retention_rate: diagnostics.date_sensitivity_retention_rate,
          neighbor_support_minutes: diagnostics.neighbor_support_minutes,
          primary_secondary_margin_percent: diagnostics.primary_secondary_margin_percent,
          cluster_mass_ratio: diagnostics.cluster_mass_ratio,
          unstable_event_ids: diagnostics.unstable_event_ids,
          most_discriminating_layers: diagnostics.most_discriminating_layers,
          event_date_sensitivity: diagnostics.event_date_sensitivity,
          candidate_splits: diagnostics.candidate_splits,
        },
        missing_layers: data.missing_layers,
        can_confirm_exact_minute: data.can_confirm_exact_minute,
      };
    },
  });

  const featuresTool = createTool({
    id: "rectification-candidate-features",
    description:
      "Compute the static chart features (ascendant degree, divisional ascendants, arudha signs, available/blocked layers) for each candidate minute in a range, without event scoring. Use this to reason about which layers each candidate actually has when interpreting a split or a transition.",
    inputSchema: z.object({
      candidate_range: candidateRangeSchema,
    }).strict(),
    execute: async (input) => {
      requireServerCandidateRange(input.candidate_range, ctx.candidateRange);
      const data = await postEngine(base, "/api/rectification/v5/candidate-features", {
        birth_date: ctx.birth.birth_date,
        start_time: input.candidate_range.start_time,
        end_time: input.candidate_range.end_time,
        lat: ctx.birth.lat,
        lon: ctx.birth.lon,
        tz: ctx.birth.tz,
        events: [],
      });
      const snapshot = (data.candidate_feature_snapshot && typeof data.candidate_feature_snapshot === "object")
        ? data.candidate_feature_snapshot as Record<string, unknown>
        : {};
      const features = Array.isArray(snapshot.features) ? (snapshot.features as unknown[]).slice(0, 24) : [];
      return {
        endpoint: data.endpoint,
        algorithm_version: data.algorithm_version,
        calculation_spec_hash: data.calculation_spec_hash,
        candidate_count: snapshot.candidate_count,
        features,
        can_confirm_exact_minute: data.can_confirm_exact_minute,
      };
    },
  });

  const confirmTool = createTool({
    id: "rectification-confirm",
    description:
      "Run the high-rigor confirmation gate for the candidate range and the user's dated events: three-engine parity, external VedAstro validation, neighbor stability, leave-one-out retention, width and margin thresholds. Returns whether a precise minute can be confirmed, the representative minute, and the reasons. Only call once you have enough confirmed dated events across domains. This does NOT write anything.",
    inputSchema: z.object({
      candidate_range: candidateRangeSchema,
      events: z.array(agenticRectificationEventSchema).min(1).max(40),
    }).strict(),
    execute: async (input) => {
      requireServerCandidateRange(input.candidate_range, ctx.candidateRange);
      const body = {
        birth_date: ctx.birth.birth_date,
        start_time: input.candidate_range.start_time,
        end_time: input.candidate_range.end_time,
        lat: ctx.birth.lat,
        lon: ctx.birth.lon,
        tz: ctx.birth.tz,
        events: input.events.map(toV3Event),
        high_rigor: true,
      };
      const data = await postEngine(base, "/api/active_rectification_events", body);
      const winning = (data.winning_segment && typeof data.winning_segment === "object")
        ? data.winning_segment as Record<string, unknown>
        : null;
      const technique = (data.technique_contract && typeof data.technique_contract === "object")
        ? data.technique_contract as Record<string, unknown>
        : null;
      const gates = (technique?.gates && typeof technique.gates === "object")
        ? technique.gates as Record<string, unknown>
        : {};
      const confirmationAllowed = technique?.confirmation_allowed === true
        && technique?.decision === "confirm_minute";
      const representativeTime = winning ? String(winning.representative_time ?? "") : "";
      if (confirmationAllowed && representativeTime) {
        confirmedGate = { time: representativeTime, resultId: String(data.result_id ?? "") };
      }
      return {
        endpoint: data.endpoint,
        result_id: data.result_id,
        confidence: data.confidence,
        event_count: data.event_count,
        domain_count: data.domain_count,
        can_apply: data.can_apply === true,
        confirmation_allowed: confirmationAllowed,
        representative_time: representativeTime,
        winning_segment: winning ? {
          start_time: winning.start_time,
          end_time: winning.end_time,
          width_minutes: winning.width_minutes,
        } : null,
        reasons: Array.isArray(data.reasons) ? data.reasons : [],
        stability_diagnostics: data.stability_diagnostics,
        technique_contract: {
          decision: technique?.decision,
          confirmation_allowed: technique?.confirmation_allowed,
          can_narrow_to_minute: technique?.can_narrow_to_minute,
          external_engines: technique?.external_engines,
          gates: {
            event_quality: gates.event_quality,
            cross_domain_coverage: gates.cross_domain_coverage,
            local_candidate: gates.local_candidate,
            required_layers: gates.required_layers,
            neighbor_stability: gates.neighbor_stability,
            leave_one_event_out: gates.leave_one_event_out,
            three_engine_input_parity: gates.three_engine_input_parity,
            vedastro_official_response: gates.vedastro_official_response,
            vedastro_minute_sensitive_validation: gates.vedastro_minute_sensitive_validation,
          },
          hard_blockers: technique?.hard_blockers,
          boundary: technique?.boundary,
        },
        missing_layers: data.missing_layers,
        candidate_ranking_summary: Array.isArray(data.candidate_ranking_summary)
          ? (data.candidate_ranking_summary as unknown[]).slice(0, 5)
          : [],
        boundary: data.boundary,
      };
    },
  });

  const saveTool = createTool({
    id: "rectification-save-birth-time",
    description:
      "Persist a confirmed birth minute to the user's profile. REQUIRES that rectification-confirm returned confirmation_allowed=true in this same session, that you have the user's explicit consent to overwrite their birth time, and that the requested time exactly equals the confirmed representative minute. Any other time is rejected. Returns whether the profile was updated.",
    inputSchema: z.object({
      time: z.string().regex(timePattern),
    }).strict(),
    execute: async (input) => {
      if (!confirmedGate) {
        return {
          ok: false,
          reason: "no_confirmed_gate: run rectification-confirm first and require confirmation_allowed=true before saving.",
        };
      }
      if (input.time !== confirmedGate.time) {
        return {
          ok: false,
          reason: `time_mismatch: the engine confirmed ${confirmedGate.time}, not ${input.time}. Only the confirmed minute can be saved.`,
        };
      }
      const applied = await ctx.applyConfirmedBirthTime(input.time);
      if (!applied.ok) {
        return { ok: false, reason: `profile_write_failed: ${applied.reason}` };
      }
      return { ok: true, saved_time: applied.saved_time, result_id: confirmedGate.resultId };
    },
  });

  return {
    "rectification-gate": gateTool,
    "rectification-scan": scanTool,
    "rectification-score": scoreTool,
    "rectification-diagnostics": diagnosticsTool,
    "rectification-candidate-features": featuresTool,
    "rectification-confirm": confirmTool,
    "rectification-save-birth-time": saveTool,
  };
}

export type AgenticRectificationTools = ReturnType<typeof createAgenticRectificationTools>;
