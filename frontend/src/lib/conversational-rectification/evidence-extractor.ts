import { createHash } from "node:crypto";
import type { RectificationEvidenceDomain } from "./technical-packet.ts";

export type ExtractedLifeEventEvidence = {
  readonly id: string;
  readonly rawText: string;
  readonly domain: RectificationEvidenceDomain;
  readonly eventSummary: string;
  readonly dateValue: string | null;
  readonly datePrecision: "day" | "month" | "year" | "unknown";
  readonly extractionStatus: "clear" | "needs_clarification" | "corrected";
  readonly scoreable: boolean;
};

export type ExtractLifeEventEvidenceInput = {
  readonly rawText: string;
  readonly sourceTurnId: string;
  readonly asOfDate: string;
  readonly correctionOfEvidenceIds?: readonly string[];
};

type ParsedDate = {
  readonly value: string;
  readonly precision: "day" | "month" | "year";
};

const chineseDatePattern = /(?:19|20)\d{2}\s*年(?:\s*\d{1,2}\s*月(?:\s*\d{1,2}\s*(?:日|号))?)?/g;
const isoDatePattern = /(?:19|20)\d{2}-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12]\d|3[01]))?/g;

function normalizedDate(value: string): ParsedDate | null {
  const chinese = value.match(/^((?:19|20)\d{2})\s*年(?:\s*(\d{1,2})\s*月(?:\s*(\d{1,2})\s*(?:日|号))?)?$/);
  const iso = value.match(/^((?:19|20)\d{2})-(\d{2})(?:-(\d{2}))?$/);
  const match = chinese ?? iso;
  if (!match) return null;
  const year = Number(match[1]);
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

function datesIn(value: string): ParsedDate[] {
  const matches = [...value.matchAll(chineseDatePattern), ...value.matchAll(isoDatePattern)]
    .sort((left, right) => (left.index ?? 0) - (right.index ?? 0));
  return matches.flatMap((match) => {
    const parsed = normalizedDate(match[0]);
    return parsed ? [parsed] : [];
  });
}

function eventSummary(fragment: string): string {
  const withoutDates = fragment
    .replace(chineseDatePattern, "")
    .replace(isoDatePattern, "")
    .replace(/^\s*(?:更正|纠正|修正)\s*[:：]?\s*/, "")
    .replace(/^\s*(?:后来|然后|同时|又)\s*/, "")
    .trim()
    .replace(/^[，,、:：\s]+|[，,、:：\s]+$/g, "");
  return withoutDates || fragment.trim();
}

function classifyDomain(summary: string): RectificationEvidenceDomain {
  if (/毕业|入学|升学|转学|学校|专业|考试|留学|学业/.test(summary)) return "education";
  if (/搬家|迁居|外地|异地|离乡|移居|出国|住所|居住/.test(summary)) return "relocation";
  if (/结婚|恋爱|分手|离婚|订婚|伴侣|关系/.test(summary)) return "relationship";
  if (/生育|孩子|父亲|母亲|父母|家人|家庭|亲人/.test(summary)) return "family";
  if (/工作|入职|离职|辞职|升职|创业|职业|公司|项目/.test(summary)) return "career";
  return "other";
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

function splitSentences(value: string): string[][] {
  const sentences = value.split(/[。！？!?；;]/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
    .map((sentence) => sentence.split(/\s*(?:并且|并|以及|同时|然后|后来又|又|，|,)\s*/)
      .map((fragment) => fragment.trim())
      .filter(Boolean));
  return sentences.length > 0 ? sentences : [[value.trim()]];
}

export function extractLifeEventEvidence(
  input: ExtractLifeEventEvidenceInput,
): readonly ExtractedLifeEventEvidence[] {
  if (!input.rawText.trim()) throw new TypeError("life-event raw text is required");
  if (!input.sourceTurnId.trim()) throw new TypeError("source turn id is required");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(input.asOfDate)) throw new TypeError("asOfDate must be YYYY-MM-DD");
  const corrections = [...(input.correctionOfEvidenceIds ?? [])];
  const events: ExtractedLifeEventEvidence[] = [];

  for (const fragments of splitSentences(input.rawText.normalize("NFKC"))) {
    const sentenceDates = datesIn(fragments.join("并"));
    const sharedDate = sentenceDates.length === 1 ? sentenceDates[0] ?? null : null;
    for (const fragment of fragments) {
      const ownDates = datesIn(fragment);
      const date = ownDates.length === 1 ? ownDates[0] ?? null : sharedDate;
      const summary = eventSummary(fragment);
      const complete = summary.length > 0 && date !== null;
      const extractionStatus = !complete
        ? "needs_clarification"
        : corrections.length > 0 ? "corrected" : "clear";
      events.push({
        id: evidenceId(input, events.length, summary),
        rawText: input.rawText,
        domain: classifyDomain(summary),
        eventSummary: summary,
        dateValue: date?.value ?? null,
        datePrecision: date?.precision ?? "unknown",
        extractionStatus,
        scoreable: complete && !dateIsFuture(date, input.asOfDate),
      });
    }
  }
  return events;
}
