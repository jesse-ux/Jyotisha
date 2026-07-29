import { z } from "zod";
import {
  rectificationV4ApiResponseSchema,
  rectificationV4HandoffSchema,
  rectificationV4JobSchema,
  type RectificationV4ApiResponse,
  type RectificationV4Handoff,
  type RectificationV4Job,
} from "./contracts";

const errorSchema = z.object({
  error: z.string().optional(),
  message: z.string().optional(),
}).passthrough();

function errorMessage(payload: unknown, fallback: string): string {
  const parsed = errorSchema.safeParse(payload);
  return parsed.success ? parsed.data.message || parsed.data.error || fallback : fallback;
}

export class RectificationV4RequestError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
}

async function json<T>(response: Response, schema: z.ZodType<T>): Promise<T> {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new RectificationV4RequestError(
      response.status,
      errorMessage(payload, "暂时无法处理，请稍后再试。"),
    );
  }
  return schema.parse(payload);
}

function post(path: string, body: unknown): Promise<RectificationV4ApiResponse> {
  return fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  }).then((response) => json(response, rectificationV4ApiResponseSchema));
}

export async function loadActiveRectificationV4(): Promise<RectificationV4ApiResponse | null> {
  const response = await fetch("/api/rectification/v4/cases/active", { cache: "no-store" });
  if (response.status === 204) return null;
  return json(response, rectificationV4ApiResponseSchema);
}

export function createRectificationV4(): Promise<RectificationV4ApiResponse> {
  return post("/api/rectification/v4/cases", { actionId: globalThis.crypto.randomUUID() });
}

export async function loadRectificationV4(caseId: string): Promise<RectificationV4ApiResponse> {
  return json(await fetch(`/api/rectification/v4/cases/${caseId}`, { cache: "no-store" }), rectificationV4ApiResponseSchema);
}

export function answerRectificationV4(caseId: string, expectedCaseVersion: number, answer: string, modelId?: string | null) {
  return post(`/api/rectification/v4/cases/${caseId}/answers`, {
    actionId: globalThis.crypto.randomUUID(), expectedCaseVersion, answer, modelId: modelId || null,
  });
}

export function regenerateRectificationV4Question(caseId: string, expectedCaseVersion: number) {
  return post(`/api/rectification/v4/cases/${caseId}/regenerate`, {
    actionId: globalThis.crypto.randomUUID(), expectedCaseVersion,
  });
}

export function transitionRectificationV4(
  caseId: string,
  expectedCaseVersion: number,
  action: "pause" | "resume" | "abandon",
) {
  return post(`/api/rectification/v4/cases/${caseId}/${action}`, {
    actionId: globalThis.crypto.randomUUID(), expectedCaseVersion,
  });
}

export function acceptRectificationV4Range(
  caseId: string,
  expectedCaseVersion: number,
  startTime: string,
  endTime: string,
) {
  return post(`/api/rectification/v4/cases/${caseId}/accept-range`, {
    actionId: globalThis.crypto.randomUUID(), expectedCaseVersion, startTime, endTime,
  });
}

export async function loadRectificationV4Job(jobId: string): Promise<RectificationV4Job> {
  const schema = z.object({ job: rectificationV4JobSchema }).strict();
  return (await json(await fetch(`/api/rectification/v4/jobs/${jobId}`, { cache: "no-store" }), schema)).job;
}


const handoffClaimActions = new Map<string, string>();

async function handoffPayload(response: Response): Promise<unknown> {
  if (response.status === 204) return null;
  return response.json().catch(() => null);
}

async function handoffPost(body: Readonly<Record<string, unknown>>): Promise<RectificationV4Handoff> {
  const serialized = JSON.stringify(body);
  let lastError: unknown;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await fetch("/api/rectification/v4/handoff", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: serialized,
      });
      const payload = await handoffPayload(response);
      if (!response.ok) {
        throw new RectificationV4RequestError(
          response.status,
          errorMessage(payload, "暂时无法保存或继续原问题，请稍后重试。"),
        );
      }
      return rectificationV4HandoffSchema.parse(payload);
    } catch (error) {
      lastError = error;
      if (error instanceof RectificationV4RequestError || attempt > 0) throw error;
    }
  }
  throw lastError;
}

export async function loadRectificationV4Handoff(caseId?: string): Promise<RectificationV4Handoff | null> {
  const query = caseId ? `?caseId=${encodeURIComponent(caseId)}` : "";
  const response = await fetch(`/api/rectification/v4/handoff${query}`, { cache: "no-store" });
  const payload = await handoffPayload(response);
  if (response.status === 204) return null;
  if (!response.ok) {
    throw new RectificationV4RequestError(
      response.status,
      errorMessage(payload, "暂时无法读取原问题，请稍后再试。"),
    );
  }
  return rectificationV4HandoffSchema.parse(payload);
}

export function attachRectificationV4Question(input: Readonly<{
  caseId: string;
  caseVersion: number;
  question: string;
  actionId: string;
}>): Promise<RectificationV4Handoff> {
  return handoffPost({ type: "attach", ...input, question: input.question.trim() });
}

export async function claimRectificationV4Handoff(input: Readonly<{
  caseId: string;
  caseVersion: number;
  question: string;
}>): Promise<RectificationV4Handoff & Readonly<{ claimActionId: string }>> {
  const identity = JSON.stringify([input.caseId, input.caseVersion, input.question.trim()]);
  const actionId = handoffClaimActions.get(identity) ?? globalThis.crypto.randomUUID();
  handoffClaimActions.set(identity, actionId);
  const result = await handoffPost({ type: "claim", ...input, actionId, question: input.question.trim() });
  if (result.status !== "claimed") handoffClaimActions.delete(identity);
  return Object.freeze({ ...result, claimActionId: actionId });
}
