import { z } from "zod";
import { lifeEventSchema } from "./birth-time-evidence.ts";
import type {
  EvidenceDatePrecision,
  EvidenceDomain,
  QuestionSpec,
} from "./birth-time-question-planner.ts";

const caseIdSchema = z.string().uuid();
const actionIdSchema = z.string().uuid();
const turnVersionSchema = z.number().int().nonnegative();

export const birthTimeGuideRequestSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("render_question"),
    caseId: caseIdSchema,
  }).strict(),
  z.object({
    type: z.literal("draft_evidence"),
    caseId: caseIdSchema,
    actionId: actionIdSchema,
    turnVersion: turnVersionSchema,
    message: z.string().trim().min(1).max(500),
  }).strict(),
  z.object({
    type: z.literal("generate_dynamic_question"),
    caseId: caseIdSchema,
    actionId: actionIdSchema,
    turnVersion: turnVersionSchema,
  }).strict(),
  z.object({
    type: z.literal("reframe_unmatched"),
    caseId: caseIdSchema,
    actionId: actionIdSchema,
    turnVersion: turnVersionSchema,
    questionId: z.string().uuid(),
    note: z.string().trim().max(240).default(""),
  }).strict(),
]).readonly();

export type BirthTimeGuideRequest = z.infer<typeof birthTimeGuideRequestSchema>;

export const guideQuestionVariants = ["direct", "gentle"] as const;
export const guideQuestionVariantSchema = z.enum(guideQuestionVariants);
const guideQuestionOutputSchema = z.object({
  variant: guideQuestionVariantSchema,
}).strict().readonly();

export const evidenceDraftModelOutputSchema = z.object({
  domain: z.enum(["education", "relocation", "relationship", "career", "finance", "health_pressure"]),
  precision: z.enum(["year", "month", "day"]).nullable(),
  date: z.string().trim().min(1).max(10).nullable(),
}).strict().readonly();

export const guideQuestionResponseSchema = z.object({
  type: z.literal("question"),
  caseId: caseIdSchema,
  turnVersion: turnVersionSchema,
  questionId: z.string().trim().min(1).max(120),
  question: z.string().trim().min(4).max(120),
  source: z.enum(["agent", "fallback"]),
}).strict().readonly();

export const guideDraftEnvelopeSchema = z.object({
  type: z.literal("evidence_draft"),
  actionId: actionIdSchema,
  requestedTurnVersion: turnVersionSchema,
  turn: z.unknown(),
}).strict().readonly();

export type GuideQuestionResponse = z.infer<typeof guideQuestionResponseSchema>;

export type ParsedEvidenceDraft = {
  readonly domain: EvidenceDomain;
  readonly precision: EvidenceDatePrecision | null;
  readonly date: string | null;
  readonly needsReview: boolean;
};

export interface BirthTimeGuideGenerator {
  generate(prompt: string): Promise<{ readonly text: string }>;
}

export class BirthTimeGuideOutputError extends Error {
  readonly name = "BirthTimeGuideOutputError";
  readonly reason: "invalid_json" | "invalid_question" | "domain_tamper" | "repeated_question";

  constructor(
    reason: "invalid_json" | "invalid_question" | "domain_tamper" | "repeated_question",
  ) {
    super(`Birth-time guide output ${reason}`);
    this.reason = reason;
  }
}

const subjectByDomain = {
  education: "一次明显的升学、转学或学习方向变化",
  relocation: "一次搬家、离乡或长期居住地变化",
  relationship: "一次关系进入、关系结束或关系明显转变",
  career: "一次明显的工作、职业方向或身份变化",
  finance: "一次收入、资产、负债或资源渠道的明显变化",
  health_pressure: "一次持续的健康压力或生活压力变化",
} as const satisfies Readonly<Record<EvidenceDomain, string>>;

function precisionQuestion(question: QuestionSpec): string {
  const requested = new Set(question.requestedPrecision);
  const labels = [
    requested.has("year") ? "哪一年" : null,
    requested.has("month") ? "哪一月" : null,
    requested.has("day") ? "哪一天" : null,
  ].filter((label): label is string => label !== null);
  return labels.length > 0 ? labels.join("或") : "什么时间";
}

export function renderQuestionVariant(
  question: QuestionSpec,
  variant: (typeof guideQuestionVariants)[number],
): string {
  const subject = subjectByDomain[question.domain];
  const timing = precisionQuestion(question);
  switch (variant) {
    case "direct":
      return `请回想${subject}，大约发生在${timing}？`;
    case "gentle":
      return `如果方便回想，${subject}大约发生在${timing}？`;
  }
}

export function fallbackQuestionCopy(question: QuestionSpec): string {
  return renderQuestionVariant(question, "direct");
}

export function parseJsonObject(text: string): unknown {
  const normalized = text.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
  const start = normalized.indexOf("{");
  const end = normalized.lastIndexOf("}");
  if (start < 0 || end <= start) throw new BirthTimeGuideOutputError("invalid_json");
  try {
    return JSON.parse(normalized.slice(start, end + 1));
  } catch (error) {
    if (error instanceof SyntaxError) throw new BirthTimeGuideOutputError("invalid_json");
    throw error;
  }
}

export function parseGuideQuestionOutput(value: unknown, question: QuestionSpec): string {
  const parsed = guideQuestionOutputSchema.safeParse(value);
  if (!parsed.success) throw new BirthTimeGuideOutputError("invalid_question");
  return renderQuestionVariant(question, parsed.data.variant);
}

function normalizeNumerals(value: string): string {
  return value.normalize("NFKC").replace(/[\u00a0\s]+/g, " ");
}

function isoDateIsGrounded(source: string, date: string): boolean {
  const escaped = date.replaceAll("-", "\\-");
  return new RegExp(`(?:^|[^0-9A-Za-z-])${escaped}(?=$|[^0-9A-Za-z-])`).test(source);
}

function chineseDateIsGrounded(source: string, date: string): boolean {
  const parts = date.split("-").map(Number);
  const year = parts[0];
  if (year === undefined || !Number.isInteger(year)) return false;
  let expression = `(?:^|[^0-9])${year}\\s*年`;
  const month = parts[1];
  if (month !== undefined) {
    if (!Number.isInteger(month)) return false;
    expression += `\\s*0?${month}\\s*月`;
  }
  const day = parts[2];
  if (day !== undefined) {
    if (!Number.isInteger(day)) return false;
    expression += `\\s*0?${day}\\s*(?:日|号)`;
  }
  return new RegExp(expression).test(source);
}

function dateIsGrounded(date: string, sourceMessage: string): boolean {
  const source = normalizeNumerals(sourceMessage).trim();
  if (/^(19|20)\d{2}$/.test(date)) {
    return source === date || chineseDateIsGrounded(source, date);
  }
  return chineseDateIsGrounded(source, date) || isoDateIsGrounded(source, date);
}

export function parseEvidenceDraftOutput(
  value: unknown,
  context: {
    readonly requiredDomain: EvidenceDomain;
    readonly sourceMessage?: string;
  },
): ParsedEvidenceDraft {
  const parsed = evidenceDraftModelOutputSchema.parse(value);
  if (parsed.domain !== context.requiredDomain) {
    throw new BirthTimeGuideOutputError("domain_tamper");
  }
  if (
    parsed.date !== null
    && context.sourceMessage !== undefined
    && !dateIsGrounded(parsed.date, context.sourceMessage)
  ) {
    return { domain: context.requiredDomain, precision: null, date: null, needsReview: true };
  }
  const complete = parsed.precision !== null
    && parsed.date !== null
    && lifeEventSchema.safeParse({
      id: "00000000-0000-4000-8000-000000000000",
      domain: parsed.domain,
      precision: parsed.precision,
      date: parsed.date,
    }).success;
  return { ...parsed, needsReview: !complete };
}

export function renderQuestionPrompt(): string {
  return JSON.stringify({
    task: "select_question_variant",
    allowedVariants: guideQuestionVariants,
  });
}

export function draftEvidencePrompt(question: QuestionSpec, message: string): string {
  return JSON.stringify({
    task: "draft_evidence",
    serverQuestion: fallbackQuestionCopy(question),
    requiredDomain: question.domain,
    requestedPrecision: question.requestedPrecision,
    userMessage: message,
  });
}
