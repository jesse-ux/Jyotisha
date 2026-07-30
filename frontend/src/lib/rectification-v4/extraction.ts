import { randomUUID } from "node:crypto";
import { extractLifeEventEvidence, parseDeclaredDateText, validatedModelAssistedEvidence, type ExtractedLifeEventEvidence } from "../conversational-rectification/evidence-extractor.ts";
import type { EvidenceProposal } from "../rectification-agent/contracts.ts";
import type {
  EventKind,
  EvidenceDomain,
  EventDateRange,
  EventSubject,
  LifeEventRevision,
  PendingEvidence,
  RelatedPerson,
  Scoreability,
} from "./contracts.ts";
import { dateRangeFromDeclared } from "./date-range.ts";
import { appendEventRevision, eventDateProvenance, latestEventRevisions } from "./evidence-ledger.ts";

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


function inferredTargetDateRange(dateText: string, target: LifeEventRevision, asOfDate: string): EventDateRange | null {
  const normalized = dateText.normalize("NFKC").trim();
  const parsed = parseDeclaredDateText(normalized, asOfDate);
  if (parsed) return dateRangeFromDeclared(parsed.value, parsed.precision);
  const year = target.dateRange.start.slice(0, 4);
  const partial = normalized.match(/^(\d{1,2})\s*月(?:\s*(\d{1,2})\s*(?:日|号))?$/u);
  if (partial) {
    const completed = parseDeclaredDateText(`${year}年${partial[1]}月${partial[2] ? `${partial[2]}号` : ""}`, asOfDate);
    if (!completed) return null;
    return { ...dateRangeFromDeclared(completed.value, completed.precision), label: normalized };
  }
  if (normalized === "上半年" || normalized === "下半年") {
    return normalized === "上半年"
      ? { start: `${year}-01-01`, end: `${year}-06-30`, precision: "range", label: normalized }
      : { start: `${year}-07-01`, end: `${year}-12-31`, precision: "range", label: normalized };
  }
  const monthRange = normalized.match(/^(\d{1,2})\s*月\s*(?:至|到|[-–—])\s*(\d{1,2})\s*月$/u);
  if (!monthRange) return null;
  const startMonth = Number(monthRange[1]);
  const endMonth = Number(monthRange[2]);
  if (startMonth < 1 || endMonth > 12 || startMonth > endMonth) return null;
  const endDay = new Date(Date.UTC(Number(year), endMonth, 0)).getUTCDate();
  return {
    start: `${year}-${String(startMonth).padStart(2, "0")}-01`,
    end: `${year}-${String(endMonth).padStart(2, "0")}-${String(endDay).padStart(2, "0")}`,
    precision: "range",
    label: normalized,
  };
}

const kindDomain: Readonly<Record<EventKind, EvidenceDomain>> = {
  education_milestone: "education",
  relocation: "relocation",
  relationship_start: "relationship",
  relationship_end: "relationship",
  relationship_change: "relationship",
  career_change: "career",
  finance_change: "finance",
  self_health_event: "health_pressure",
  family_health_event: "family",
  family_bereavement: "family",
  family_event: "family",
  other: "other",
};

const kindEvidence: Readonly<Record<EventKind, RegExp>> = {
  education_milestone: /(?:入学|毕业|升学|退学|考试|学业)/u,
  relocation: /(?:搬家|搬到|迁居|迁往|住校|移居)/u,
  relationship_start: /(?:开始|恋爱|在一起|交往|结婚)/u,
  relationship_end: /(?:分手|离婚|结束|分开|断联|破裂)/u,
  relationship_change: /(?:关系变化|感情变化|复合)/u,
  career_change: /(?:工作|入职|离职|换岗|创业|升职|实习)/u,
  finance_change: /(?:收入|亏损|投资|负债|财务|破产)/u,
  self_health_event: /(?:我|本人|自己).*(?:生病|手术|住院|健康)/u,
  family_health_event: /(?:家人|父亲|母亲|爸爸|妈妈|祖父母|伴侣).*(?:生病|手术|住院|健康)/u,
  family_bereavement: /(?:去世|离世|过世|丧亲)/u,
  family_event: /(?:家人|家庭|父亲|母亲|爸爸|妈妈|兄弟|姐妹)/u,
  other: /(?:其他|别的)/u,
};

function groundedReclassification(target: LifeEventRevision, proposal: EvidenceProposal): boolean {
  const explicitCorrection = /(?:不是|并非|不对|错了)/u.test(proposal.sourceSpan)
    && /(?:而是|其实是|实际是|应该是|发生在.+身上|是)/u.test(proposal.sourceSpan);
  if (!explicitCorrection) return false;
  const changed = target.domain !== proposal.proposedDomain
    || target.eventKind !== proposal.proposedEventKind
    || target.subject !== proposal.proposedSubject
    || target.relatedPerson !== proposal.proposedRelatedPerson;
  if (!changed || kindDomain[proposal.proposedEventKind] !== proposal.proposedDomain) return false;
  if (target.eventKind !== proposal.proposedEventKind && !kindEvidence[proposal.proposedEventKind].test(proposal.sourceSpan)) return false;
  if (!proposal.sourceSpan.includes(proposal.proposedSummary)) return false;
  if (target.subject !== proposal.proposedSubject) {
    const subjectPattern = proposal.proposedSubject === "self" ? /(?:我|本人|自己)/u
      : proposal.proposedSubject === "family" ? /(?:家人|父亲|母亲|爸爸|妈妈|祖父母|兄弟|姐妹)/u
        : proposal.proposedSubject === "partner" ? /(?:伴侣|配偶|对象|男友|女友|丈夫|妻子)/u
          : /(?:其他人|别人)/u;
    if (!subjectPattern.test(proposal.sourceSpan)) return false;
  }
  if (target.relatedPerson !== proposal.proposedRelatedPerson && proposal.proposedRelatedPerson) {
    const relatedPattern: Readonly<Record<RelatedPerson, RegExp>> = {
      father: /(?:父亲|爸爸)/u, mother: /(?:母亲|妈妈)/u,
      sibling: /(?:兄弟|姐妹|哥哥|弟弟|姐姐|妹妹)/u,
      partner: /(?:伴侣|配偶|对象|男友|女友|丈夫|妻子)/u,
      grandparent: /(?:祖父母|爷爷|奶奶|外公|外婆)/u,
    };
    if (!relatedPattern[proposal.proposedRelatedPerson].test(proposal.sourceSpan)) return false;
  }
  return true;
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
    ...eventDateProvenance(target),
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
            ...eventDateProvenance(target),
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


export function stageAgentEvidenceProposals(input: Readonly<{
  caseId: string;
  rawText: string;
  sourceTurnId: string;
  asOfDate: string;
  existing: readonly LifeEventRevision[];
  proposals: readonly EvidenceProposal[];
  now?: Date;
}>): ReconciledV4Evidence {
  const revisions: LifeEventRevision[] = [];
  const pending: PendingEvidence[] = [];
  const active = latestEventRevisions(input.existing);
  for (const proposal of input.proposals) {
    if (proposal.operation === "ignore") continue;
    const target = proposal.targetEventId ? active.find((event) => event.eventId === proposal.targetEventId) ?? null : null;
    if (!input.rawText.includes(proposal.sourceSpan)) {
      pending.push(pendingEvidence({ caseId: input.caseId, turnId: input.sourceTurnId, rawText: input.rawText, reasonCode: "event_unparsed", targetEventId: proposal.targetEventId, now: input.now }));
      continue;
    }
    if (proposal.operation === "revise_date") {
      const dateRange = target && proposal.dateText && input.rawText.includes(proposal.dateText)
        ? inferredTargetDateRange(proposal.dateText, target, input.asOfDate)
        : null;
      if (!target || !dateRange || dateRange.start > input.asOfDate) {
        pending.push(pendingEvidence({ caseId: input.caseId, turnId: input.sourceTurnId, rawText: input.rawText, reasonCode: proposal.dateText ? "event_unparsed" : "date_unresolved", targetEventId: proposal.targetEventId, now: input.now }));
        continue;
      }
      revisions.push(appendEventRevision([...input.existing, ...revisions], {
        eventId: target.eventId,
        domain: target.domain,
        eventKind: target.eventKind,
        subject: target.subject,
        relatedPerson: target.relatedPerson,
        summary: target.summary,
        rawText: input.rawText,
        dateRange,
        ...eventDateProvenance(target),
        scoreability: target.scoreability,
      }, { now: input.now }));
      continue;
    }
    if (proposal.operation === "reclassify") {
      if (!target || !groundedReclassification(target, proposal)) {
        pending.push(pendingEvidence({ caseId: input.caseId, turnId: input.sourceTurnId, rawText: input.rawText, reasonCode: "event_unparsed", targetEventId: proposal.targetEventId, now: input.now }));
        continue;
      }
      const identityChanged = target.subject !== proposal.proposedSubject || target.relatedPerson !== proposal.proposedRelatedPerson;
      revisions.push(appendEventRevision([...input.existing, ...revisions], {
        eventId: target.eventId,
        domain: proposal.proposedDomain,
        eventKind: proposal.proposedEventKind,
        subject: proposal.proposedSubject,
        relatedPerson: proposal.proposedRelatedPerson,
        summary: proposal.proposedSummary,
        rawText: input.rawText,
        dateRange: target.dateRange,
        ...eventDateProvenance(target),
        scoreability: identityChanged ? "pending_review" : target.scoreability,
      }, { now: input.now }));
      continue;
    }
    if (!proposal.dateText || !input.rawText.includes(proposal.dateText)) {
      pending.push(pendingEvidence({ caseId: input.caseId, turnId: input.sourceTurnId, rawText: input.rawText, reasonCode: proposal.dateText ? "event_unparsed" : "date_unresolved", targetEventId: null, now: input.now }));
      continue;
    }
    const extracted = validatedModelAssistedEvidence({
      rawText: input.rawText,
      sourceTurnId: input.sourceTurnId,
      asOfDate: input.asOfDate,
      extraction: {
        sourceSpan: proposal.sourceSpan,
        summary: proposal.proposedSummary,
        domain: proposal.proposedDomain,
        eventKind: proposal.proposedEventKind,
        subject: proposal.proposedSubject,
        relatedPerson: proposal.proposedRelatedPerson,
        dateText: proposal.dateText,
      },
    });
    if (!extracted?.dateValue || extracted.datePrecision === "unknown") {
      pending.push(pendingEvidence({ caseId: input.caseId, turnId: input.sourceTurnId, rawText: input.rawText, reasonCode: "event_unparsed", targetEventId: null, now: input.now }));
      continue;
    }
    const revision = newRevision(extracted, [...input.existing, ...revisions], input.now);
    if (revision && !revisions.some((value) => value.eventId === revision.eventId)) revisions.push(revision);
  }
  return {
    revisions,
    pending,
    unansweredTargetEventId: null,
    targetDisposition: revisions.length ? "resolved" : "unresolved",
  };
}
