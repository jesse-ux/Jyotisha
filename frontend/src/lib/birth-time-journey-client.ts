import { z } from "zod";
import { journeySnapshotSchema } from "./birth-time-journey.ts";

const answerSchema = z.enum(["A", "B", "C", "D"]);
const questionnaireSchema = z.object({
  questions: z.array(z.object({
    id: z.string(),
    prompt: z.string(),
    options: z.array(z.object({
      key: answerSchema,
      label: z.string(),
    })).optional(),
  })),
  samples: z.array(z.object({
    ascendantSign: z.string().nullable(),
    d9Sign: z.string().nullable(),
    d10Sign: z.string().nullable(),
  })),
  raw: z.record(z.unknown()),
});

const scoringSchema = z.object({
  answeredCount: z.number().int().min(0),
  candidateClusterRankings: z.array(z.object({
    cluster: z.string(),
    score: z.number(),
  })),
  raw: z.record(z.unknown()),
});

const journeyResponseSchema = z.object({
  caseId: z.string().uuid(),
  snapshot: journeySnapshotSchema,
  questionnaire: questionnaireSchema.nullable(),
  scoring: scoringSchema.nullable(),
  answers: z.record(answerSchema).default({}),
}).superRefine((value, context) => {
  if (value.snapshot.route === "rectification" && value.snapshot.canApply) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["snapshot", "canApply"],
      message: "rectification results cannot apply an exact time",
    });
  }
  if (value.snapshot.route === "direct_chart" && !value.snapshot.activeTime) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["snapshot", "activeTime"],
      message: "direct chart requires an active time",
    });
  }
});

const errorPayloadSchema = z.object({
  message: z.string().optional(),
  error: z.string().optional(),
});

export type JourneyClientResponse = z.infer<typeof journeyResponseSchema>;
export type JourneyAnswer = z.infer<typeof answerSchema>;

export class BirthTimeJourneyRequestError extends Error {
  readonly name = "BirthTimeJourneyRequestError";
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function parseJourneyResponse(value: unknown): JourneyClientResponse {
  return journeyResponseSchema.parse(value);
}

async function responsePayload(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch (error) {
    if (error instanceof SyntaxError) return null;
    throw error;
  }
}

async function sendJourneyEvent(event: Readonly<Record<string, unknown>>) {
  const response = await fetch("/api/birth-time-journey", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(event),
  });
  const payload = await responsePayload(response);
  if (!response.ok) {
    const parsedError = errorPayloadSchema.safeParse(payload);
    const message = parsedError.success
      ? parsedError.data.message ?? parsedError.data.error ?? "生时评估暂时不可用"
      : "生时评估暂时不可用";
    throw new BirthTimeJourneyRequestError(response.status, message);
  }
  return parseJourneyResponse(payload);
}

export function requestBirthTimeAssessment() {
  return sendJourneyEvent({ type: "assess" });
}

export function answerBirthTimeQuestion(
  caseId: string,
  questionId: string,
  answer: JourneyAnswer,
) {
  return sendJourneyEvent({ type: "answer_question", caseId, questionId, answer });
}

export function resumeBirthTimeJourney(caseId: string) {
  return sendJourneyEvent({ type: "resume", caseId });
}
