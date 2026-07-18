"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fallbackQuestionCopy } from "@/lib/birth-time-guide-agent";
import {
  confirmBirthTimeEvidenceDraft,
  draftBirthTimeEvidence,
  pauseBirthTimeRectification,
  pollBirthTimeScoring,
  requestBirthTimeGuidePrompt,
  resumeBirthTimeJourney,
  skipBirthTimeEvidenceQuestion,
} from "@/lib/birth-time-journey-client";
import type { JourneyClientResponse } from "@/lib/birth-time-journey-client";
import {
  confirmGuidedBirthTimeCandidate,
  reviseBirthTimeEvidenceDraft,
  saveGuidedBirthTimeCandidate,
} from "@/lib/birth-time-guided-client";
import { confirmReviewedBirthTimeDraft } from "@/lib/birth-time-guided-draft-confirmation";
import {
  createIdentityRequestCache,
  publishCurrentJourney,
  scheduleCancellableStart,
} from "@/lib/birth-time-guided-effect-coordinator";
import { runBirthTimeScoringPoll, scoringPollDelay } from "@/lib/birth-time-guided-polling";
import type { EvidenceDatePrecision } from "@/lib/birth-time-question-planner";

type GuidedJourneyInput = {
  readonly journey: JourneyClientResponse | null;
  readonly preview: boolean;
  readonly onJourney: (journey: JourneyClientResponse) => void;
  readonly onReady: (journey: JourneyClientResponse) => void;
  readonly onEditBirthTimeDetails: () => void;
};

export type BirthTimeGuidedController = {
  readonly question: string;
  readonly pending: boolean;
  readonly error: string;
  readonly pollRecoverable: boolean;
  readonly submitMessage: (message: string) => void;
  readonly confirmDraft: (precision: EvidenceDatePrecision, date: string) => void;
  readonly skip: () => void;
  readonly pause: () => void;
  readonly resume: () => void;
  readonly editBirthTimeDetails: () => void;
  readonly acknowledgeReady: () => void;
  readonly retryScoring: () => void;
  readonly saveCandidate: (resultId: string) => void;
  readonly confirmCandidate: (resultId: string, time: string) => void;
};

const guidePromptRequests = createIdentityRequestCache<Awaited<ReturnType<typeof requestBirthTimeGuidePrompt>>>();

function questionFrom(turn: JourneyClientResponse): string {
  const action = turn.nextAction;
  return action.kind === "ask_baseline_evidence" || action.kind === "ask_adaptive_evidence"
    ? fallbackQuestionCopy(action.question)
    : "";
}

export function useBirthTimeGuidedJourney(input: GuidedJourneyInput): BirthTimeGuidedController {
  const { journey, onJourney, onReady, onEditBirthTimeDetails, preview } = input;
  const latest = useRef(journey);
  const busy = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [agentQuestion, setAgentQuestion] = useState<{ readonly key: string; readonly text: string } | null>(null);
  const [pollRun, setPollRun] = useState(0);

  useEffect(() => {
    latest.current = journey;
  }, [journey]);

  const operate = useCallback((operation: (
    turn: JourneyClientResponse,
    publishIntermediate: (turn: JourneyClientResponse) => void,
  ) => Promise<JourneyClientResponse>) => {
    const current = journey;
    if (!current || busy.current) return;
    let expected = current;
    busy.current = true;
    setPending(true);
    setError("");
    const publishIntermediate = (turn: JourneyClientResponse) => {
      if (publishCurrentJourney({
        expected,
        current: latest.current,
        next: turn,
        publish: onJourney,
      })) {
        expected = turn;
        latest.current = turn;
      }
    };
    void operation(current, publishIntermediate).then((turn) => {
      if (publishCurrentJourney({
        expected,
        current: latest.current,
        next: turn,
        publish: onJourney,
      })) latest.current = turn;
    }).catch((caught: unknown) => {
      setError(caught instanceof Error ? caught.message : "当前步骤暂时无法完成，请重试。");
    }).finally(() => {
      busy.current = false;
      setPending(false);
    });
  }, [journey, onJourney]);

  const actionId = () => globalThis.crypto.randomUUID();

  useEffect(() => {
    const turn = journey;
    if (!turn) return;
    const action = turn.nextAction;
    if (action.kind !== "ask_baseline_evidence" && action.kind !== "ask_adaptive_evidence") return;
    const key = `${turn.caseId}:${turn.turnVersion}:${action.question.questionId}`;
    if (preview) return;
    let active = true;
    void guidePromptRequests.run(key, () => requestBirthTimeGuidePrompt(turn.caseId)).then((response) => {
      if (active && response.turnVersion === turn.turnVersion && response.questionId === action.question.questionId) {
        setAgentQuestion({ key, text: response.question });
      }
    }).catch(() => {
      if (active) setAgentQuestion(null);
    });
    return () => { active = false; };
  }, [journey, preview]);

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
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : "暂时无法读取评分进度，请稍后重试。");
        }
      });
    });
    return () => {
      cancelStart();
      controller.abort();
    };
  }, [
    pollIdentity,
    onJourney,
    preview,
    pollRun,
  ]);

  const submitMessage = (message: string) => operate((turn) => {
    if (preview) return Promise.resolve(turn);
    return draftBirthTimeEvidence(turn.caseId, actionId(), turn.turnVersion, message).then((value) => value.turn);
  });

  const confirmDraft = (precision: EvidenceDatePrecision, date: string) => operate(async (turn, publishIntermediate) => {
    if (preview) return turn;
    return confirmReviewedBirthTimeDraft({ turn, precision, date }, {
      createActionId: actionId,
      revise: reviseBirthTimeEvidenceDraft,
      publish: publishIntermediate,
      confirm: (command) => confirmBirthTimeEvidenceDraft(
        command.caseId,
        command.actionId,
        command.turnVersion,
        command.draftId,
      ),
    });
  });

  const skip = () => operate((turn) => preview ? Promise.resolve(turn) : skipBirthTimeEvidenceQuestion(turn.caseId, actionId(), turn.turnVersion));
  const pause = () => operate((turn) => preview ? Promise.resolve(turn) : pauseBirthTimeRectification(turn.caseId, actionId(), turn.turnVersion));
  const resume = () => operate((turn) => preview ? Promise.resolve(turn) : resumeBirthTimeJourney(turn.caseId));
  const acknowledgeReady = () => {
    if (journey?.nextAction.kind === "ready") onReady(journey);
  };
  const retryScoring = () => {
    const turn = journey;
    if (turn?.nextAction.kind === "score_pending") {
      setError("");
      setPollRun((value) => value + 1);
      return;
    }
    operate((current) => current.nextAction.kind === "retry_scoring" && !preview
      ? pollBirthTimeScoring(current.caseId, current.nextAction.jobId)
      : Promise.resolve(current));
  };
  const saveCandidate = (resultId: string) => operate((turn) => preview ? Promise.resolve(turn) : saveGuidedBirthTimeCandidate({ caseId: turn.caseId, actionId: actionId(), turnVersion: turn.turnVersion, resultId }));
  const confirmCandidate = (resultId: string, time: string) => operate((turn) => preview ? Promise.resolve(turn) : confirmGuidedBirthTimeCandidate({ caseId: turn.caseId, actionId: actionId(), turnVersion: turn.turnVersion, resultId, time }));

  const turn = journey;
  const fallback = turn ? questionFrom(turn) : "";
  const action = turn?.nextAction;
  const key = turn && (action?.kind === "ask_baseline_evidence" || action?.kind === "ask_adaptive_evidence")
    ? `${turn.caseId}:${turn.turnVersion}:${action.question.questionId}`
    : "";
  return {
    question: agentQuestion?.key === key ? agentQuestion.text : fallback,
    pending,
    error,
    pollRecoverable: Boolean(error) && action?.kind === "score_pending",
    submitMessage,
    confirmDraft,
    skip,
    pause,
    resume,
    editBirthTimeDetails: onEditBirthTimeDetails,
    acknowledgeReady,
    retryScoring,
    saveCandidate,
    confirmCandidate,
  };
}
