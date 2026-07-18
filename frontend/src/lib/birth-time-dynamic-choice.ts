import { z } from "zod";

const timeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);

export const publicChoiceKindSchema = z.enum(["primary", "unknown", "unmatched"]);

export type PublicChoiceKind = z.infer<typeof publicChoiceKindSchema>;

export const timeRangeSchema = z.object({
  startTime: timeSchema,
  endTime: timeSchema,
}).strict().readonly();

export type TimeRange = {
  readonly startTime: string;
  readonly endTime: string;
};

export const publicDynamicChoiceOptionSchema = z.object({
  optionId: z.string().trim().min(1),
  label: z.string().trim().min(1).max(80),
  kind: publicChoiceKindSchema,
}).strict().readonly();

export type PublicDynamicChoiceQuestion = {
  readonly questionId: string;
  readonly prompt: string;
  readonly options: readonly {
    readonly optionId: string;
    readonly label: string;
    readonly kind: PublicChoiceKind;
  }[];
};

function validateOptionSet(
  value: { readonly options: readonly { readonly optionId: string; readonly kind: PublicChoiceKind }[] },
  context: z.RefinementCtx,
): void {
  const primaryCount = value.options.filter((option) => option.kind === "primary").length;
  const unknownCount = value.options.filter((option) => option.kind === "unknown").length;
  const unmatchedCount = value.options.filter((option) => option.kind === "unmatched").length;
  if (primaryCount < 2 || primaryCount > 4) {
    context.addIssue({ code: z.ZodIssueCode.custom, path: ["options"], message: "questions require two to four primary options" });
  }
  if (unknownCount !== 1) {
    context.addIssue({ code: z.ZodIssueCode.custom, path: ["options"], message: "questions require one unknown option" });
  }
  if (unmatchedCount !== 1) {
    context.addIssue({ code: z.ZodIssueCode.custom, path: ["options"], message: "questions require one unmatched option" });
  }
  if (new Set(value.options.map((option) => option.optionId)).size !== value.options.length) {
    context.addIssue({ code: z.ZodIssueCode.custom, path: ["options"], message: "question option ids must be unique" });
  }
}

export const publicDynamicChoiceQuestionSchema = z.object({
  questionId: z.string().trim().min(1),
  prompt: z.string().trim().min(1).max(240),
  options: z.array(publicDynamicChoiceOptionSchema).readonly(),
}).strict().superRefine(validateOptionSet).readonly();

export { validateOptionSet };
