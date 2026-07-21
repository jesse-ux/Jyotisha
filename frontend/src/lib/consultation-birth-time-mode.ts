import { z } from "zod";
import {
  guardGeneralNoBirthTimeOutput,
  guardPreciseTimingOutput,
} from "./timing-output-guard.ts";

export const consultationBirthTimeModeSchema = z.enum([
  "verified_chart",
  "unverified_birth_time",
  "general_no_birth_time",
]);

export type ConsultationBirthTimeMode = z.infer<typeof consultationBirthTimeModeSchema>;

export const UNVERIFIED_BIRTH_TIME_NOTICE = "使用未校正填报时间；分钟敏感结论的置信度已降低。";

export function shouldRunBirthChartWorkflow(mode: ConsultationBirthTimeMode): boolean {
  return mode !== "general_no_birth_time";
}

export function applyBirthTimeModeToWorkflowContext<
  T extends {
    consumer_context: {
      answer_policy: Record<string, unknown>;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  },
>(context: T, mode: ConsultationBirthTimeMode): T {
  if (mode !== "unverified_birth_time") return context;
  return {
    ...context,
    consumer_context: {
      ...context.consumer_context,
      answer_policy: {
        ...context.consumer_context.answer_policy,
        can_answer_precise_timing: false,
        birth_time_confidence: "unverified_reported_time",
        candidate_is_confirmed: false,
      },
    },
  };
}

/**
 * Server-side output boundary. Timing and guarantee filtering remains active
 * without inserting a rectification warning into every answer.
 */
export function createBirthTimeModeOutputGuard(
  mode: ConsultationBirthTimeMode,
  canAnswerPreciseTiming: boolean,
): (text: string) => string {
  return (text) => {
    return mode === "general_no_birth_time"
      ? guardGeneralNoBirthTimeOutput(text)
      : canAnswerPreciseTiming ? text : guardPreciseTimingOutput(text);
  };
}
