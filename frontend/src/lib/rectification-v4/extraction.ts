import { extractLifeEventEvidence } from "../conversational-rectification/evidence-extractor.ts";
import type { EventKind, EvidenceDomain, LifeEventRevision } from "./contracts.ts";
import { dateRangeFromDeclared } from "./date-range.ts";
import { appendEventRevision, latestEventRevisions } from "./evidence-ledger.ts";

function eventKind(domain: EvidenceDomain, summary: string): EventKind {
  if (domain === "relationship") {
    return /分手|离婚|结束|断联|分开|破裂/.test(summary) ? "relationship_end" : "relationship_start";
  }
  switch (domain) {
    case "education": return "education_milestone";
    case "relocation": return "relocation";
    case "career": return "career_change";
    case "finance": return "finance_change";
    case "health_pressure": return "health_event";
    case "family": return "family_event";
    case "other": return "other";
  }
}

export function extractV4EventRevisions(input: {
  readonly answer: string;
  readonly sourceTurnId: string;
  readonly asOfDate: string;
  readonly existing: readonly LifeEventRevision[];
  readonly targetEventId?: string | null;
  readonly now?: Date;
}): readonly LifeEventRevision[] {
  const extracted = extractLifeEventEvidence({
    rawText: input.answer,
    sourceTurnId: input.sourceTurnId,
    asOfDate: input.asOfDate,
  });
  const target = input.targetEventId
    ? latestEventRevisions(input.existing).find((event) => event.eventId === input.targetEventId) ?? null
    : null;
  if (input.targetEventId) {
    if (!target) throw new Error("rectification_v4_target_event_not_found");
    const event = extracted.find((value) => value.dateValue && value.datePrecision !== "unknown");
    if (!event?.dateValue || event.datePrecision === "unknown") return [];
    const dateRange = dateRangeFromDeclared(event.dateValue, event.datePrecision);
    if (dateRange.start > input.asOfDate) return [];
    return [appendEventRevision(input.existing, {
      eventId: target.eventId,
      domain: target.domain,
      eventKind: target.eventKind,
      summary: target.summary,
      rawText: input.answer,
      dateRange,
      scoreability: target.scoreability,
    }, { id: event.id, now: input.now })];
  }
  return extracted.flatMap((event) => {
    if (!event.dateValue || event.datePrecision === "unknown") return [];
    const domain = event.domain as EvidenceDomain;
    return [appendEventRevision(input.existing, {
      eventId: event.id,
      domain,
      eventKind: eventKind(domain, event.eventSummary),
      summary: event.eventSummary,
      rawText: event.rawText,
      dateRange: dateRangeFromDeclared(event.dateValue, event.datePrecision),
    }, { id: event.id, now: input.now })];
  });
}
