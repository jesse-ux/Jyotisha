import { randomUUID } from "node:crypto";
import { extractLifeEventEvidence, type ExtractedLifeEventEvidence } from "../conversational-rectification/evidence-extractor.ts";
import type {
  EventKind,
  EvidenceDomain,
  EventSubject,
  LifeEventRevision,
  PendingEvidence,
  RelatedPerson,
  Scoreability,
} from "./contracts.ts";
import { dateRangeFromDeclared } from "./date-range.ts";
import { appendEventRevision, latestEventRevisions } from "./evidence-ledger.ts";

const allowedKinds = new Set<EventKind>([
  "education_milestone", "relocation", "relationship_start", "relationship_end", "relationship_change",
  "career_change", "finance_change", "self_health_event", "family_health_event", "family_bereavement", "family_event", "other",
]);
const missingEventSummary = "事件内容待补充";
const directionChangePattern = /(?:换一个|换个问题|问别的|换个方向|都不符合|不是这个|不聊这个)/;
const declinedPattern = /(?:不想说|不方便说|不想回答|跳过|这个不说)/;
const unknownPattern = /(?:不知道|不清楚|记不清|不确定|没印象|忘了|想不起来)/;

export type TargetDisposition =
  | "resolved"
  | "unknown"
  | "declined"
  | "direction_change"
  | "answered_other_event"
  | "unresolved"
  | "not_applicable";

function explicitDisposition(answer: string): TargetDisposition | null {
  if (directionChangePattern.test(answer)) return "direction_change";
  if (declinedPattern.test(answer)) return "declined";
  if (unknownPattern.test(answer)) return "unknown";
  return null;
}

function normalizeKind(domain: EvidenceDomain, value: string, summary: string): EventKind {
  if (allowedKinds.has(value as EventKind)) return value as EventKind;
  if (domain === "relationship") return /分手|离婚|结束|断联|分开|破裂/.test(summary) ? "relationship_end" : "relationship_start";
  return ({ education: "education_milestone", relocation: "relocation", career: "career_change", finance: "finance_change", health_pressure: "self_health_event", family: "family_event", other: "other" } as const)[domain];
}

function pendingEvidence(input: {
  caseId: string;
  turnId: string;
  rawText: string;
  reasonCode: PendingEvidence["reasonCode"];
  targetEventId: string | null;
  now?: Date;
}): PendingEvidence {
  return {
    id: randomUUID(),
    caseId: input.caseId,
    turnId: input.turnId,
    rawText: input.rawText.trim(),
    reasonCode: input.reasonCode,
    targetEventId: input.targetEventId,
    resolvedEventId: null,
    createdAt: (input.now ?? new Date()).toISOString(),
    resolvedAt: null,
  };
}

function newRevision(event: ExtractedLifeEventEvidence, existing: readonly LifeEventRevision[], now?: Date): LifeEventRevision | null {
  if (!event.dateValue || event.datePrecision === "unknown") return null;
  const domain = event.domain as EvidenceDomain;
  return appendEventRevision(existing, {
    eventId: event.id,
    domain,
    eventKind: normalizeKind(domain, event.eventKind, event.eventSummary),
    subject: event.subject as EventSubject,
    relatedPerson: event.relatedPerson as RelatedPerson | null,
    summary: event.eventSummary,
    rawText: event.rawText,
    dateRange: dateRangeFromDeclared(event.dateValue, event.datePrecision),
    scoreability: event.scoreability as Scoreability,
  }, { id: event.id, now });
}

function describesTarget(event: ExtractedLifeEventEvidence, target: LifeEventRevision): boolean {
  if (event.eventSummary === missingEventSummary) return true;
  const eventKind = normalizeKind(event.domain as EvidenceDomain, event.eventKind, event.eventSummary);
  if (event.domain !== target.domain || eventKind !== target.eventKind) return false;
  return event.rawText.includes(target.summary)
    || event.eventSummary.includes(target.summary)
    || target.summary.includes(event.eventSummary);
}

function subjectRevision(answer: string, target: LifeEventRevision, existing: readonly LifeEventRevision[], now?: Date): LifeEventRevision | null {
  const compact = answer.trim().replace(/[。！!，,；;\s]/g, "");
  let subject: EventSubject | null = null;
  if (/^(我|本人|我本人|我自己|是我|发生在我身上)$/.test(compact)) subject = "self";
  else if (/^(家人|我的家人|父亲|母亲|爸爸|妈妈|祖父母|爷爷|奶奶|外公|外婆)$/.test(compact)) subject = "family";
  else if (/^(伴侣|配偶|对象|男友|女友|丈夫|妻子|老公|老婆)$/.test(compact)) subject = "partner";
  if (!subject) return null;

  const healthEvent = target.eventKind === "self_health_event" || target.eventKind === "family_health_event";
  const domain: EvidenceDomain = healthEvent ? (subject === "self" ? "health_pressure" : "family") : target.domain;
  const eventKind: EventKind = healthEvent ? (subject === "self" ? "self_health_event" : "family_health_event") : target.eventKind;
  const scoreability: Scoreability = subject === "self" && domain !== "family" && domain !== "other" ? "scoreable" : "context_only";
  const relatedPerson: RelatedPerson | null = subject === "partner" ? "partner" : subject === "family" ? target.relatedPerson : null;
  return appendEventRevision(existing, {
    eventId: target.eventId,
    domain,
    eventKind,
    subject,
    relatedPerson,
    summary: target.summary,
    rawText: answer,
    dateRange: target.dateRange,
    scoreability,
  }, { now });
}

export type ReconciledV4Evidence = Readonly<{
  revisions: readonly LifeEventRevision[];
  pending: readonly PendingEvidence[];
  unansweredTargetEventId: string | null;
  targetDisposition: TargetDisposition;
}>;

export function reconcileV4Evidence(input: {
  readonly caseId: string;
  readonly answer: string;
  readonly sourceTurnId: string;
  readonly asOfDate: string;
  readonly existing: readonly LifeEventRevision[];
  readonly targetEventId?: string | null;
  readonly assistedEvidence?: readonly ExtractedLifeEventEvidence[];
  readonly now?: Date;
}): ReconciledV4Evidence {
  const deterministic = extractLifeEventEvidence({ rawText: input.answer, sourceTurnId: input.sourceTurnId, asOfDate: input.asOfDate });
  const extracted = [...(input.assistedEvidence ?? []), ...deterministic];
  const target = input.targetEventId ? latestEventRevisions(input.existing).find((event) => event.eventId === input.targetEventId) ?? null : null;
  if (input.targetEventId && !target) throw new Error("rectification_v4_target_event_not_found");

  const revisions: LifeEventRevision[] = [];
  const consumed = new Set<string>();
  let unresolvedReason: PendingEvidence["reasonCode"] | null = null;
  let targetResolved = !target;

  if (target) {
    const clarified = subjectRevision(input.answer, target, input.existing, input.now);
    if (clarified) {
      revisions.push(clarified);
      targetResolved = true;
    } else {
      const targetAnswer = extracted.find((event) => event.dateValue && event.datePrecision !== "unknown" && describesTarget(event, target));
      if (targetAnswer?.dateValue && targetAnswer.datePrecision !== "unknown") {
        const dateRange = dateRangeFromDeclared(targetAnswer.dateValue, targetAnswer.datePrecision);
        if (dateRange.start <= input.asOfDate) {
          revisions.push(appendEventRevision(input.existing, {
            eventId: target.eventId,
            domain: target.domain,
            eventKind: target.eventKind,
            subject: target.subject,
            relatedPerson: target.relatedPerson,
            summary: target.summary,
            rawText: input.answer,
            dateRange,
            scoreability: target.scoreability,
          }, { id: targetAnswer.id, now: input.now }));
          consumed.add(targetAnswer.id);
          targetResolved = true;
        }
      }
    }
  }

  for (const event of extracted) {
    if (consumed.has(event.id) || revisions.some((revision) => revision.id === event.id)) continue;
    const revision = newRevision(event, [...input.existing, ...revisions], input.now);
    if (revision && revision.dateRange.start <= input.asOfDate) {
      if (!revisions.some((value) => value.eventId === revision.eventId)) revisions.push(revision);
      continue;
    }
    unresolvedReason = event.datePrecision === "unknown" ? "date_unresolved" : "event_unparsed";
  }

  const explicit = explicitDisposition(input.answer);
  const addedOtherEvent = target
    ? revisions.some((revision) => revision.eventId !== target.eventId)
    : false;
  const targetDisposition: TargetDisposition = explicit ?? (!target
    ? "not_applicable"
    : targetResolved ? "resolved" : addedOtherEvent ? "answered_other_event" : "unresolved");
  const suppressPending = targetDisposition === "unknown"
    || targetDisposition === "declined"
    || targetDisposition === "direction_change";
  if (extracted.length === 0 && !suppressPending) unresolvedReason = "event_unparsed";
  const pending = unresolvedReason && !suppressPending ? [
    pendingEvidence({
      caseId: input.caseId,
      turnId: input.sourceTurnId,
      rawText: input.answer,
      reasonCode: unresolvedReason,
      targetEventId: target?.eventId ?? null,
      now: input.now,
    }),
  ] : [];

  return {
    revisions,
    pending,
    unansweredTargetEventId: target && (targetDisposition === "unresolved" || targetDisposition === "answered_other_event") ? target.eventId : null,
    targetDisposition,
  };
}

export function extractV4EventRevisions(input: Omit<Parameters<typeof reconcileV4Evidence>[0], "caseId"> & { readonly caseId?: string }): readonly LifeEventRevision[] {
  return reconcileV4Evidence({ ...input, caseId: input.caseId ?? "00000000-0000-4000-8000-000000000000" }).revisions;
}
