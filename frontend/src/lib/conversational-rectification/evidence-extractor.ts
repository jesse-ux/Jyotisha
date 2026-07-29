import { createHash } from "node:crypto";
import type { RectificationEvidenceDomain } from "./technical-packet.ts";

export type ExtractedLifeEventEvidence = {
  readonly id: string;
  readonly rawText: string;
  readonly domain: RectificationEvidenceDomain;
  readonly eventKind: string;
  readonly subject: "self" | "family" | "partner" | "other";
  readonly relatedPerson: "father" | "mother" | "grandparent" | "sibling" | "partner" | null;
  readonly eventSummary: string;
  readonly dateValue: string | null;
  readonly datePrecision: "day" | "month" | "year" | "unknown";
  readonly extractionStatus: "clear" | "needs_clarification" | "corrected";
  readonly scoreability: "scoreable" | "context_only" | "pending_review" | "unsupported";
  readonly scoreable: boolean;
  readonly correctsEvidenceIds: readonly string[];
};

export type ExtractLifeEventEvidenceInput = {
  readonly rawText: string;
  readonly sourceTurnId: string;
  readonly asOfDate: string;
  readonly correctsEvidenceId?: string;
};

type ParsedDate = {
  readonly value: string;
  readonly precision: "day" | "month" | "year";
};

const chineseDatePattern = /(?:1\d{3}|20\d{2}|\d{2})\s*年(?:\s*\d{1,2}\s*月(?:\s*\d{1,2}\s*(?:日|号))?)?/g;
const isoDatePattern = /(?:1\d{3}|20\d{2})-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12]\d|3[01]))?/g;
const unresolvedRelativeTimePattern = /(?:来年|次年|第二年|翌年|后来|此前|同年|当年|那年|随后|先前|然后|之前|之后|今年|去年|前年|明年)/;
const leadingRelativeTimePattern = /^\s*(?:(?:来年|次年|第二年|翌年|后来(?:又)?|此前|同年|当年|那年|随后|先前|然后|之前|之后|今年|去年|前年|明年)\s*)+/;
const missingEventSummary = "事件内容待补充";

export function parseDeclaredDateText(value: string, asOfDate: string): ParsedDate | null {
  const chinese = value.match(/^((?:1\d{3}|20\d{2}|\d{2}))\s*年(?:\s*(\d{1,2})\s*月(?:\s*(\d{1,2})\s*(?:日|号))?)?$/);
  const iso = value.match(/^((?:1\d{3}|20\d{2}))-(\d{2})(?:-(\d{2}))?$/);
  const match = chinese ?? iso;
  if (!match) return null;
  const rawYear = match[1] ?? "";
  const asOfYear = Number(asOfDate.slice(0, 4));
  const currentCentury = Math.floor(asOfYear / 100) * 100;
  const expandedYear = currentCentury + Number(rawYear);
  const year = rawYear.length === 2
    ? expandedYear <= asOfYear ? expandedYear : expandedYear - 100
    : Number(rawYear);
  const rawMonth = match[2];
  if (!rawMonth) return { value: String(year), precision: "year" };
  const month = Number(rawMonth);
  if (month < 1 || month > 12) return null;
  const rawDay = match[3];
  if (!rawDay) {
    return { value: `${year}-${String(month).padStart(2, "0")}`, precision: "month" };
  }
  const day = Number(rawDay);
  const candidate = new Date(Date.UTC(year, month - 1, day));
  if (candidate.getUTCFullYear() !== year
    || candidate.getUTCMonth() !== month - 1
    || candidate.getUTCDate() !== day) return null;
  return {
    value: `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`,
    precision: "day",
  };
}

function datesIn(value: string, asOfDate: string): ParsedDate[] {
  const matches = [...value.matchAll(chineseDatePattern), ...value.matchAll(isoDatePattern)]
    .sort((left, right) => (left.index ?? 0) - (right.index ?? 0));
  return matches.flatMap((match) => {
    const parsed = parseDeclaredDateText(match[0], asOfDate);
    return parsed ? [parsed] : [];
  });
}

function eventSummary(fragment: string): string {
  const withoutDates = fragment
    .replace(chineseDatePattern, "")
    .replace(isoDatePattern, "")
    .replace(/(?:发生时间|事件详情)\s*[:：]\s*/g, "")
    .replace(/^\s*(?:更正|纠正|修正)\s*[:：]?\s*/, "")
    .replace(leadingRelativeTimePattern, "")
    .replace(/^\s*(?:同时|又)\s*/, "")
    .trim()
    .replace(/^[，,、:：\s]+|[，,、:：\s]+$/g, "");
  return /[A-Za-z0-9\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/.test(withoutDates)
    ? withoutDates
    : missingEventSummary;
}

type EventSemantics = Readonly<{
  domain: RectificationEvidenceDomain;
  eventKind: string;
  subject: "self" | "family" | "partner" | "other";
  relatedPerson: "father" | "mother" | "grandparent" | "sibling" | "partner" | null;
  scoreability: "scoreable" | "context_only" | "pending_review" | "unsupported";
}>;

function classifyEvent(summary: string): EventSemantics {
  const familyPerson = summary.match(/(父亲|爸爸|母亲|妈妈|爷爷|奶奶|外公|外婆|祖父|祖母|外祖父|外祖母|兄弟|姐妹|伴侣|配偶|丈夫|妻子|老公|老婆|男友|女友|儿子|女儿|孩子)/);
  if (familyPerson && /确诊|疾病|癌症|肿瘤|手术|住院|受伤|事故|车祸|交通事故|创伤|康复|病危|重病|去世|离世|死亡|丧亲|葬礼/.test(summary)) {
    const relatedPerson = /父亲|爸爸/.test(familyPerson[1])
      ? "father"
      : /母亲|妈妈/.test(familyPerson[1])
        ? "mother"
        : /爷爷|奶奶|外公|外婆|祖父|祖母|外祖父|外祖母/.test(familyPerson[1])
          ? "grandparent"
          : /兄弟|姐妹/.test(familyPerson[1])
            ? "sibling"
            : /伴侣|配偶|丈夫|妻子|老公|老婆|男友|女友/.test(familyPerson[1])
              ? "partner"
              : null;
    const bereavement = /去世|离世|死亡|丧亲|葬礼/.test(summary);
    return {
      domain: "family",
      eventKind: bereavement ? "family_bereavement" : "family_health_event",
      subject: "family",
      relatedPerson,
      scoreability: "context_only",
    };
  }
  if (/确诊|疾病|癌症|肿瘤|手术|住院|受伤|事故|车祸|交通事故|创伤|康复|病危|健康/.test(summary)) {
    return { domain: "health_pressure", eventKind: "self_health_event", subject: "self", relatedPerson: null, scoreability: "scoreable" };
  }
  if (/毕业|入学|升学|转学|学校|大学|专业|考试|考(?:了)?(?:一)?次?研|研究生(?:入学)?考试|留学|学业|学习/.test(summary)) {
    return { domain: "education", eventKind: "education_milestone", subject: "self", relatedPerson: null, scoreability: "scoreable" };
  }
  if (/搬家|迁居|外地|异地|离乡|移居|出国|住所|居住/.test(summary)) {
    return { domain: "relocation", eventKind: "relocation", subject: "self", relatedPerson: null, scoreability: "scoreable" };
  }
  if (/结婚|恋爱|分手|离婚|订婚|伴侣|关系/.test(summary)) {
    return { domain: "relationship", eventKind: "relationship_change", subject: /伴侣|配偶/.test(summary) ? "partner" : "self", relatedPerson: /伴侣|配偶/.test(summary) ? "partner" : null, scoreability: "scoreable" };
  }
  if (/生育|孩子|父亲|母亲|父母|家人|家庭|亲人/.test(summary)) {
    return { domain: "family", eventKind: "family_event", subject: "family", relatedPerson: null, scoreability: "context_only" };
  }
  if (/收入|工资|薪资|奖金|财富|财务|投资|亏损|盈利|负债|债务|资产/.test(summary)) {
    return { domain: "finance", eventKind: "finance_change", subject: "self", relatedPerson: null, scoreability: "scoreable" };
  }
  if (/工作|实习|研究员|入职|离职|辞职|升职|创业|职业|职位|任职|负责|管理职责|公司|项目/.test(summary)) {
    return { domain: "career", eventKind: "career_change", subject: "self", relatedPerson: null, scoreability: "scoreable" };
  }
  return { domain: "other", eventKind: "other", subject: "other", relatedPerson: null, scoreability: "unsupported" };
}

function dateIsFuture(date: ParsedDate, asOfDate: string): boolean {
  switch (date.precision) {
    case "year": return date.value > asOfDate.slice(0, 4);
    case "month": return date.value > asOfDate.slice(0, 7);
    case "day": return date.value > asOfDate;
  }
}

function evidenceId(input: ExtractLifeEventEvidenceInput, index: number, summary: string): string {
  const hex = createHash("sha256")
    .update(`${input.sourceTurnId}\0${index}\0${input.rawText}\0${summary}`)
    .digest("hex");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-4${hex.slice(13, 16)}-a${hex.slice(17, 20)}-${hex.slice(20, 32)}`;
}

function splitSentenceFragments(sentence: string): string[] {
  const fragments: string[] = [];
  const separators = /\s*(并且|并|以及|同时|然后|后来又|又|，|,)\s*/g;
  let cursor = 0;
  let prefixForNext = "";
  for (const match of sentence.matchAll(separators)) {
    const index = match.index ?? cursor;
    const fragment = sentence.slice(cursor, index).trim();
    if (fragment) {
      fragments.push(`${prefixForNext}${fragment}`);
      prefixForNext = "";
    }
    const separator = match[1] ?? "";
    if (separator === "然后" || separator === "后来又") {
      prefixForNext += separator;
    }
    cursor = index + match[0].length;
  }
  const tail = sentence.slice(cursor).trim();
  if (tail) fragments.push(`${prefixForNext}${tail}`);
  return fragments;
}

function splitSentences(value: string): string[][] {
  const sentences = value.split(/[。！？!?；;]/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
    .map(splitSentenceFragments);
  return sentences.length > 0 ? sentences : [[value.trim()]];
}

function coalesceSameEventDetails(
  input: ExtractLifeEventEvidenceInput,
  events: readonly ExtractedLifeEventEvidence[],
): readonly ExtractedLifeEventEvidence[] {
  const merged: ExtractedLifeEventEvidence[] = [];
  for (const event of events) {
    const previous = merged.at(-1);
    const canMerge = previous
      && previous.dateValue !== null
      && previous.dateValue === event.dateValue
      && previous.datePrecision === event.datePrecision
      && previous.domain === event.domain
      && previous.eventKind === event.eventKind
      && previous.subject === event.subject
      && previous.relatedPerson === event.relatedPerson
      && previous.extractionStatus === event.extractionStatus
      && previous.scoreability === event.scoreability
      && previous.scoreable === event.scoreable
      && previous.correctsEvidenceIds.join("\0") === event.correctsEvidenceIds.join("\0");
    if (!canMerge) {
      merged.push(event);
      continue;
    }
    const summaries = [...new Set([previous.eventSummary, event.eventSummary])];
    const eventSummary = summaries.join("；");
    merged[merged.length - 1] = {
      ...previous,
      id: evidenceId(input, merged.length - 1, eventSummary),
      eventSummary,
    };
  }
  return merged;
}

export function extractLifeEventEvidence(
  input: ExtractLifeEventEvidenceInput,
): readonly ExtractedLifeEventEvidence[] {
  if (!input.rawText.trim()) throw new TypeError("life-event raw text is required");
  if (!input.sourceTurnId.trim()) throw new TypeError("source turn id is required");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(input.asOfDate)) throw new TypeError("asOfDate must be YYYY-MM-DD");
  const correctionTargets = input.correctsEvidenceId ? [input.correctsEvidenceId] : [];
  const events: ExtractedLifeEventEvidence[] = [];

  for (const fragments of splitSentences(input.rawText.normalize("NFKC"))) {
    const sentenceDates = datesIn(fragments.join("并"), input.asOfDate);
    const sharedDate = sentenceDates.length === 1 ? sentenceDates[0] ?? null : null;
    for (const fragment of fragments) {
      const ownDates = datesIn(fragment, input.asOfDate);
      const unresolvedRelativeTime = ownDates.length === 0 && unresolvedRelativeTimePattern.test(fragment);
      const date = ownDates.length === 1
        ? ownDates[0] ?? null
        : ownDates.length === 0 && !unresolvedRelativeTime ? sharedDate : null;
      const summary = eventSummary(fragment);
      const semantics = classifyEvent(summary);
      const complete = summary !== missingEventSummary && date !== null && !unresolvedRelativeTime;
      const extractionStatus = !complete
        ? "needs_clarification"
        : correctionTargets.length > 0 ? "corrected" : "clear";
      const scoreable = complete && !dateIsFuture(date, input.asOfDate) && semantics.scoreability === "scoreable";
      events.push({
        id: evidenceId(input, events.length, summary),
        rawText: input.rawText,
        domain: semantics.domain,
        eventKind: semantics.eventKind,
        subject: semantics.subject,
        relatedPerson: semantics.relatedPerson,
        eventSummary: summary,
        dateValue: date?.value ?? null,
        datePrecision: date?.precision ?? "unknown",
        extractionStatus,
        scoreability: complete ? semantics.scoreability : "pending_review",
        scoreable,
        correctsEvidenceIds: correctionTargets,
      });
    }
  }
  return coalesceSameEventDetails(input, events);
}


export type ModelAssistedEventExtraction = Readonly<{
  sourceSpan: string;
  summary: string;
  domain: RectificationEvidenceDomain;
  eventKind: string;
  subject: "self" | "family" | "partner" | "other";
  relatedPerson: "father" | "mother" | "grandparent" | "sibling" | "partner" | null;
  dateText: string | null;
}>;

const allowedKindsByDomain: Readonly<Record<RectificationEvidenceDomain, readonly string[]>> = {
  education: ["education_milestone"],
  relocation: ["relocation"],
  relationship: ["relationship_start", "relationship_end", "relationship_change"],
  career: ["career_change"],
  finance: ["finance_change"],
  health_pressure: ["self_health_event"],
  family: ["family_health_event", "family_bereavement", "family_event"],
  other: ["other"],
};

const familyRelatedPeople = new Set<ModelAssistedEventExtraction["relatedPerson"]>([
  "father",
  "mother",
  "grandparent",
  "sibling",
]);
const explicitFamilySubjectMarkers = [
  "父亲", "爸爸", "老爸", "母亲", "妈妈", "老妈",
  "爷爷", "奶奶", "外公", "外婆", "祖父", "祖母", "外祖父", "外祖母",
  "兄弟", "姐妹", "家里老人", "家中老人",
] as const;

export function validatedModelAssistedEvidence(input: Readonly<{
  rawText: string;
  sourceTurnId: string;
  asOfDate: string;
  extraction: ModelAssistedEventExtraction;
}>): ExtractedLifeEventEvidence | null {
  const sourceSpan = input.extraction.sourceSpan.trim();
  const dateText = input.extraction.dateText?.trim() || null;
  if (!sourceSpan || !input.rawText.includes(sourceSpan)) return null;
  if (!dateText || !input.rawText.includes(dateText)) return null;
  const date = parseDeclaredDateText(dateText.normalize("NFKC"), input.asOfDate);
  if (!date || dateIsFuture(date, input.asOfDate)) return null;
  if (!allowedKindsByDomain[input.extraction.domain]?.includes(input.extraction.eventKind)) return null;
  const { subject, relatedPerson, domain } = input.extraction;
  if (subject === "self" && relatedPerson !== null) return null;
  if ((subject === "family") !== (domain === "family")) return null;
  if (familyRelatedPeople.has(relatedPerson) && subject !== "family") return null;
  if (relatedPerson === "partner" && (subject !== "partner" || domain !== "relationship")) return null;
  if (subject === "partner" && (domain !== "relationship" || relatedPerson !== "partner")) return null;
  if (explicitFamilySubjectMarkers.some((marker) => sourceSpan.includes(marker))
    && (subject !== "family" || domain !== "family")) return null;
  const summary = eventSummary(sourceSpan);
  if (summary === missingEventSummary) return null;
  const familyContext = input.extraction.subject === "family" || input.extraction.domain === "family";
  const scoreability = familyContext
    ? "context_only" as const
    : input.extraction.subject === "self" || (input.extraction.subject === "partner" && input.extraction.domain === "relationship")
      ? "scoreable" as const
      : "unsupported" as const;
  return {
    id: evidenceId({ rawText: input.rawText, sourceTurnId: input.sourceTurnId, asOfDate: input.asOfDate }, 0, summary),
    rawText: input.rawText,
    domain: input.extraction.domain,
    eventKind: input.extraction.eventKind,
    subject: input.extraction.subject,
    relatedPerson: input.extraction.relatedPerson,
    eventSummary: summary,
    dateValue: date.value,
    datePrecision: date.precision,
    extractionStatus: "clear",
    scoreability,
    scoreable: scoreability === "scoreable",
    correctsEvidenceIds: [],
  };
}
