import { NextResponse } from "next/server";
import { z } from "zod";
import { parseBirthTimeProfile } from "@/lib/birth-time-journey-adapters";
import { BirthProfileTimezoneError, resolveMissingBirthTimezoneOffset } from "@/lib/birth-profile-timezone";
import {
  createJyotishBirthTimeJourneyEngine,
  BirthTimeJourneyEngineError,
} from "@/lib/birth-time-journey-engine";
import { createBirthTimeJourneyService, RectificationCaseNotFoundError, RectificationQuestionsUnavailableError, type DynamicVersionedJourneyResponse, type VersionedJourneyResponse } from "@/lib/birth-time-journey-service";
import { BirthTimeJourneyActionError } from "@/lib/birth-time-journey-actions";
import { birthTimeJourneyRequestSchema } from "@/lib/birth-time-journey-request";
import { StaleJourneyTurnError } from "@/lib/birth-time-journey-turn-persistence";
import { CandidateConfirmationError } from "@/lib/birth-time-evidence";
import { BirthTimeEvidenceContextError, EvidenceRectificationCaseNotFoundError, GuidedJourneyLegacyMutationError, StaleCandidateConfirmationError } from "@/lib/birth-time-evidence-service";
import { createSupabaseBirthTimeJourneyStore, BirthTimeJourneyStoreError } from "@/lib/birth-time-journey-store";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { BirthTimeScoringJobError } from "@/lib/birth-time-scoring-job";
import { GuidedCandidateActionError } from "@/lib/birth-time-guided-candidate";
import { GuidedCandidateStoreConflictError } from "@/lib/birth-time-guided-candidate-store";
import { JourneyTurnInvariantError } from "@/lib/birth-time-journey-turn";
import { JourneyResponseInvariantError } from "@/lib/birth-time-journey-response-schema";
import { BirthTimeDynamicActionError } from "@/lib/birth-time-dynamic-actions";
import {
  recordJourneyMetricEvent,
  recordJourneyTransitionMetric,
  recordScoringJourneyMetric,
  type JourneyMetricName,
} from "@/lib/birth-time-journey-telemetry";

export const runtime = "nodejs";
export const maxDuration = 60;

async function requestPayload(request: Request): Promise<unknown> {
  try {
    return await request.json();
  } catch (error) {
    if (error instanceof SyntaxError) return null;
    throw error;
  }
}

async function responseWithJourneyMetric(
  action: Promise<VersionedJourneyResponse | DynamicVersionedJourneyResponse>,
  name: Extract<JourneyMetricName, "turn_advanced" | "draft_corrected" | "journey_paused">,
): Promise<NextResponse> {
  const response = await action;
  if (response.journeyProtocol === "dynamic-choice-v2") {
    recordJourneyMetricEvent({ kind: "transition", name, phase: "adaptive" });
  } else {
    recordJourneyTransitionMetric(response, name);
  }
  return NextResponse.json(response);
}

export async function POST(request: Request) {
  let supabase: Awaited<ReturnType<typeof createServerSupabaseClient>>;
  let journeyStoreClient: ReturnType<typeof createAdminSupabaseClient>;
  try {
    supabase = await createServerSupabaseClient();
    journeyStoreClient = createAdminSupabaseClient();
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json(
        { error: "服务尚未配置", message: "请先配置 Supabase 环境变量。" },
        { status: 503 },
      );
    }
    throw error;
  }

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: "请先登录", message: "登录后才能继续出生时间评估。" },
      { status: 401 },
    );
  }

  const parsed = birthTimeJourneyRequestSchema.safeParse(await requestPayload(request));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "生时评估请求格式不正确", details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  const service = createBirthTimeJourneyService({
    store: createSupabaseBirthTimeJourneyStore(journeyStoreClient),
    engine: createJyotishBirthTimeJourneyEngine(),
  });

  try {
    switch (parsed.data.type) {
      case "assess": {
        const { data: profile, error } = await supabase
          .from("profiles")
          .select("birth_date,reported_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,latitude,longitude,timezone_id,timezone_offset")
          .eq("id", user.id)
          .maybeSingle();
        if (error) throw new BirthTimeJourneyStoreError("load_case");
        if (!profile) {
          return NextResponse.json(
            { error: "出生资料尚未完成", message: "请先填写出生日期、时间情况和地点。" },
            { status: 409 },
          );
        }
        const assessment = parseBirthTimeProfile(await resolveMissingBirthTimezoneOffset(profile));
        return responseWithJourneyMetric(service.assess(user.id, assessment), "turn_advanced");
      }
      case "answer_question":
        return responseWithJourneyMetric(service.answerQuestion(
          user.id,
          parsed.data.caseId,
          parsed.data.questionId,
          parsed.data.answer,
        ), "turn_advanced");
      case "answer_dynamic_choice":
        return responseWithJourneyMetric(service.answerDynamicChoice(user.id, parsed.data), "turn_advanced");
      case "resume": {
        const response = await service.resume(user.id, parsed.data.caseId);
        return NextResponse.json(response);
      }
      case "poll_scoring":
        {
          const before = await service.resume(user.id, parsed.data.caseId);
          if (before.journeyProtocol === "dynamic-choice-v2") {
            const response = await service.pollDynamicScoringJob(
              user.id,
              parsed.data.caseId,
              parsed.data.jobId,
            );
            return NextResponse.json(response);
          }
          const response = await service.pollScoringJob(user.id, parsed.data.caseId, parsed.data.jobId);
          recordScoringJourneyMetric(before, response);
          return NextResponse.json(response);
        }
      case "submit_life_events":
        return responseWithJourneyMetric(service.submitLifeEvents(user.id, parsed.data.caseId, parsed.data.events), "turn_advanced");
      case "save_candidate":
        return responseWithJourneyMetric(service.saveCandidate(user.id, parsed.data.caseId, parsed.data.resultId), "turn_advanced");
      case "confirm_candidate":
        return responseWithJourneyMetric(service.confirmCandidate(user.id, parsed.data.caseId, parsed.data.resultId, parsed.data.time), "turn_advanced");
      case "confirm_evidence_draft":
        return responseWithJourneyMetric(service.confirmEvidenceDraft(user.id, parsed.data.caseId, parsed.data.actionId, parsed.data.turnVersion, parsed.data.draftId), "turn_advanced");
      case "skip_evidence_question":
        return responseWithJourneyMetric(service.skipEvidenceQuestion(user.id, parsed.data.caseId, parsed.data.actionId, parsed.data.turnVersion), "turn_advanced");
      case "pause_rectification": {
        const current = await service.resume(user.id, parsed.data.caseId);
        return responseWithJourneyMetric(current.journeyProtocol === "dynamic-choice-v2"
          ? service.pauseDynamic(user.id, parsed.data.caseId, parsed.data.actionId, parsed.data.turnVersion)
          : service.pause(user.id, parsed.data.caseId, parsed.data.actionId, parsed.data.turnVersion), "journey_paused");
      }
      case "finish_rectification": {
        const current = await service.resume(user.id, parsed.data.caseId);
        return responseWithJourneyMetric(current.journeyProtocol === "dynamic-choice-v2"
          ? service.finishDynamic(user.id, parsed.data.caseId, parsed.data.actionId, parsed.data.turnVersion)
          : service.finishWithCurrentRange(user.id, parsed.data.caseId, parsed.data.actionId, parsed.data.turnVersion), "turn_advanced");
      }
      case "revise_evidence_draft":
        return responseWithJourneyMetric(service.reviseEvidenceDraft({
          userId: user.id,
          caseId: parsed.data.caseId,
          actionId: parsed.data.actionId,
          expectedVersion: parsed.data.turnVersion,
          precision: parsed.data.precision,
          date: parsed.data.date,
        }), "draft_corrected");
      case "save_guided_candidate":
        return responseWithJourneyMetric(service.saveGuidedCandidate({
          userId: user.id,
          caseId: parsed.data.caseId,
          actionId: parsed.data.actionId,
          expectedVersion: parsed.data.turnVersion,
          resultId: parsed.data.resultId,
        }), "turn_advanced");
      case "confirm_guided_candidate":
        return responseWithJourneyMetric(service.confirmGuidedCandidate({
          userId: user.id,
          caseId: parsed.data.caseId,
          actionId: parsed.data.actionId,
          expectedVersion: parsed.data.turnVersion,
          resultId: parsed.data.resultId,
          time: parsed.data.time,
        }), "turn_advanced");
      case "confirm_dynamic_candidate":
        return responseWithJourneyMetric(service.confirmDynamicCandidate({
          userId: user.id,
          caseId: parsed.data.caseId,
          actionId: parsed.data.actionId,
          expectedVersion: parsed.data.turnVersion,
          resultId: parsed.data.resultId,
          time: parsed.data.time,
        }), "turn_advanced");
      default: {
        const exhaustive: never = parsed.data;
        return exhaustive;
      }
    }
  } catch (error) {
    if (error instanceof BirthTimeScoringJobError) {
      recordJourneyMetricEvent({ kind: "error", reason: "scoring_failure", phase: "result" });
    } else if (error instanceof JourneyTurnInvariantError || error instanceof JourneyResponseInvariantError) {
      recordJourneyMetricEvent({ kind: "error", reason: "illegal_state", phase: "result" });
    }
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "出生资料尚未完成", message: "请检查出生时间情况和地点后重试。" },
        { status: 409 },
      );
    }
    if (
      error instanceof RectificationCaseNotFoundError
      || error instanceof EvidenceRectificationCaseNotFoundError
      || (error instanceof BirthTimeJourneyActionError && error.reason === "case_not_found")
      || (error instanceof BirthTimeDynamicActionError && error.reason === "case_not_found")
      || (error instanceof GuidedCandidateActionError && error.reason === "case_not_found")
    ) {
      return NextResponse.json(
        { error: "校正记录不存在", message: "请重新开始出生时间评估。" },
        { status: 404 },
      );
    }
    if (error instanceof RectificationQuestionsUnavailableError) {
      return NextResponse.json(
        { error: "校正问题暂不可用", message: "当前资料已安全保留，请稍后重新评估。" },
        { status: 409 },
      );
    }
    if (
      error instanceof StaleJourneyTurnError
      || error instanceof BirthTimeJourneyActionError
      || (error instanceof BirthTimeDynamicActionError && error.reason !== "unavailable")
      || error instanceof GuidedJourneyLegacyMutationError
      || error instanceof BirthTimeScoringJobError
      || error instanceof GuidedCandidateActionError
      || error instanceof GuidedCandidateStoreConflictError
    ) {
      return NextResponse.json(
        { error: "校正状态已更新", message: "请使用最新问题或草稿后重试。" },
        { status: 409 },
      );
    }
    if (
      error instanceof StaleCandidateConfirmationError
      || error instanceof CandidateConfirmationError
      || error instanceof BirthTimeEvidenceContextError
    ) {
      return NextResponse.json(
        { error: "候选结果已变化", message: "请重新提交事件证据并确认最新候选结果。" },
        { status: 409 },
      );
    }
    if (error instanceof BirthProfileTimezoneError
      || error instanceof BirthTimeJourneyStoreError
      || error instanceof BirthTimeJourneyEngineError
      || (error instanceof BirthTimeDynamicActionError && error.reason === "unavailable")) {
      return NextResponse.json(
        { error: "生时评估暂时不可用", message: "已保留当前资料，请稍后重试。" },
        { status: 503 },
      );
    }
    throw error;
  }
}
