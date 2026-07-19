"use client";

import { useEffect, useState } from "react";
import { fallbackQuestionCopy } from "@/lib/birth-time-guide-agent";
import {
  generateDynamicBirthTimeQuestion,
  pollBirthTimeScoring,
  requestBirthTimeGuidePrompt,
} from "@/lib/birth-time-journey-client";
import type { JourneyClientResponse } from "@/lib/birth-time-journey-client";
import {
  createIdentityRequestCache,
  publishCurrentJourney,
  scheduleCancellableStart,
} from "@/lib/birth-time-guided-effect-coordinator";
import { runBirthTimeScoringPoll, scoringPollDelay } from "@/lib/birth-time-guided-polling";

type AutomaticEffectsInput = {
  readonly journey: JourneyClientResponse | null;
  readonly latest: { current: JourneyClientResponse | null };
  readonly preview: boolean;
  readonly pollRun: number;
  readonly generationRun: number;
  readonly onJourney: (journey: JourneyClientResponse) => void;
  readonly setError: (message: string) => void;
};

const guideRequests = createIdentityRequestCache<Awaited<ReturnType<typeof requestBirthTimeGuidePrompt>>>();
const generationRequests = createIdentityRequestCache<Awaited<ReturnType<typeof generateDynamicBirthTimeQuestion>>>();

function fallbackQuestion(turn: JourneyClientResponse): string {
  const action = turn.nextAction;
  if (turn.journeyProtocol === "dynamic-choice-v2") {
    return action.kind === "ask_dynamic_choice" ? action.question.prompt : "";
  }
  return action.kind === "ask_baseline_evidence" || action.kind === "ask_adaptive_evidence"
    ? fallbackQuestionCopy(action.question)
    : "";
}

export function useBirthTimeAutomaticJourneyEffects(input: AutomaticEffectsInput): string {
  const { generationRun, journey, latest, onJourney, pollRun, preview, setError } = input;
  const [agentQuestion, setAgentQuestion] = useState<{ readonly key: string; readonly text: string } | null>(null);

  useEffect(() => {
    const turn = journey;
    if (!turn || turn.journeyProtocol === "dynamic-choice-v2") return;
    const action = turn.nextAction;
    if (preview || (action.kind !== "ask_baseline_evidence" && action.kind !== "ask_adaptive_evidence")) return;
    const key = `${turn.caseId}:${turn.turnVersion}:${action.question.questionId}`;
    let active = true;
    void guideRequests.run(key, () => requestBirthTimeGuidePrompt(turn.caseId)).then((response) => {
      if (active && response.turnVersion === turn.turnVersion && response.questionId === action.question.questionId) {
        setAgentQuestion({ key, text: response.question });
      }
    }).catch(() => { if (active) setAgentQuestion(null); });
    return () => { active = false; };
  }, [journey, preview]);

  const generationIdentity = journey?.journeyProtocol === "dynamic-choice-v2"
    && (journey.nextAction.kind === "generate_dynamic_question"
      || journey.nextAction.kind === "retry_question_generation")
    ? `${journey.caseId}:${journey.turnVersion}`
    : "";

  useEffect(() => {
    const turn = latest.current;
    if (!turn || turn.journeyProtocol !== "dynamic-choice-v2" || preview) return;
    if (turn.nextAction.kind !== "generate_dynamic_question"
      && turn.nextAction.kind !== "retry_question_generation") return;
    const expected = turn;
    const key = `${turn.caseId}:${turn.turnVersion}`;
    void generationRequests.run(key, () => generateDynamicBirthTimeQuestion(
      turn.caseId,
      globalThis.crypto.randomUUID(),
      turn.turnVersion,
    )).then((next) => {
      if (publishCurrentJourney({ expected, current: latest.current, next, publish: onJourney })) latest.current = next;
    }).catch((caught: unknown) => {
      if (latest.current?.caseId === expected.caseId && latest.current.turnVersion === expected.turnVersion) {
        setError(caught instanceof Error ? caught.message : "暂时无法生成下一题，请重试。");
      }
    });
  }, [generationIdentity, generationRun, latest, onJourney, preview, setError]);

  const pollIdentity = journey?.nextAction.kind === "score_pending"
    ? `${journey.caseId}:${journey.turnVersion}:${journey.nextAction.jobId}`
    : "";

  useEffect(() => {
    const turn = latest.current;
    if (!turn || turn.nextAction.kind !== "score_pending" || preview) return;
    const controller = new AbortController();
    const jobId = turn.nextAction.jobId;
    const key = `${turn.caseId}:${turn.turnVersion}:${jobId}`;
    const cancelStart = scheduleCancellableStart(() => {
      void runBirthTimeScoringPoll({
        initial: turn,
        maxAttempts: 7,
        signal: controller.signal,
        delay: scoringPollDelay,
        poll: () => pollBirthTimeScoring(turn.caseId, jobId, controller.signal),
      }).then((result) => {
        const current = latest.current;
        const currentKey = current?.nextAction.kind === "score_pending"
          ? `${current.caseId}:${current.turnVersion}:${current.nextAction.jobId}`
          : "";
        if (controller.signal.aborted || currentKey !== key) return;
        onJourney(result.turn);
        latest.current = result.turn;
        if (result.kind === "exhausted") setError("评分仍在进行。你可以稍后继续，或重新检查状态。");
      }).catch((caught: unknown) => {
        if (!controller.signal.aborted) setError(caught instanceof Error ? caught.message : "暂时无法读取评分进度，请稍后重试。");
      });
    });
    return () => { cancelStart(); controller.abort(); };
  }, [latest, onJourney, pollIdentity, pollRun, preview, setError]);

  const action = journey?.nextAction;
  const key = journey && journey.journeyProtocol !== "dynamic-choice-v2"
    && (action?.kind === "ask_baseline_evidence" || action?.kind === "ask_adaptive_evidence")
    ? `${journey.caseId}:${journey.turnVersion}:${action.question.questionId}`
    : "";
  return agentQuestion?.key === key ? agentQuestion.text : journey ? fallbackQuestion(journey) : "";
}
