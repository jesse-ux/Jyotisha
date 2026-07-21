import { z } from "zod";

type ReceiptBase = {
  readonly actionId: string;
  readonly turnVersion: number;
};

export type DynamicActionReceipt = ReceiptBase & (
  | { readonly kind: "answer_choice"; readonly questionId: string; readonly optionId: string }
  | {
    readonly kind: "commit_question";
    readonly outcome: "question" | "terminal";
    readonly questionId: string | null;
    readonly questionFingerprint: string | null;
    readonly partitionFingerprint: string | null;
    readonly submittedQuestionFingerprint: string | null;
    readonly submittedPartitionFingerprint: string | null;
  }
  | { readonly kind: "unmatched_context"; readonly questionId: string; readonly note: string }
  | { readonly kind: "pause" }
  | { readonly kind: "finish" }
  | { readonly kind: "resume" }
  | { readonly kind: "confirm_candidate"; readonly resultId: string; readonly time: string }
);

const receiptBase = {
  actionId: z.string().uuid().refine((value) => value === value.toLowerCase()),
  turnVersion: z.number().int().nonnegative(),
} as const;
const identifier = z.string().trim().min(1);

export const dynamicActionReceiptSchema: z.ZodType<DynamicActionReceipt> = z.union([
  z.object({
    ...receiptBase,
    kind: z.literal("answer_choice"),
    questionId: identifier,
    optionId: identifier,
  }).strict(),
  z.object({
    ...receiptBase,
    kind: z.literal("commit_question"),
    outcome: z.literal("question"),
    questionId: identifier,
    questionFingerprint: identifier,
    partitionFingerprint: identifier,
    submittedQuestionFingerprint: identifier,
    submittedPartitionFingerprint: identifier,
  }).strict(),
  z.object({
    ...receiptBase,
    kind: z.literal("commit_question"),
    outcome: z.literal("terminal"),
    questionId: z.null(),
    questionFingerprint: z.null(),
    partitionFingerprint: z.null(),
    submittedQuestionFingerprint: identifier.nullable(),
    submittedPartitionFingerprint: identifier.nullable(),
  }).strict(),
  z.object({
    ...receiptBase,
    kind: z.literal("unmatched_context"),
    questionId: identifier,
    note: z.string().max(240),
  }).strict(),
  z.object({ ...receiptBase, kind: z.literal("pause") }).strict(),
  z.object({ ...receiptBase, kind: z.literal("finish") }).strict(),
  z.object({ ...receiptBase, kind: z.literal("resume") }).strict(),
  z.object({
    ...receiptBase,
    kind: z.literal("confirm_candidate"),
    resultId: z.string().uuid(),
    time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  }).strict(),
]).readonly();
