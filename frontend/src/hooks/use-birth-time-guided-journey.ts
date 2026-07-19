"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  answerDynamicBirthTimeChoice,
  confirmBirthTimeEvidenceDraft,
  draftBirthTimeEvidence,
  finishBirthTimeRectification,
  pauseBirthTimeRectification,
  pollBirthTimeScoring,
  reframeUnmatchedBirthTimeAnswer,
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
  claimMutation,
  publishCurrentJourney,
} from "@/lib/birth-time-guided-effect-coordinator";
import type { EvidenceDatePrecision } from "@/lib/birth-time-question-planner";
import { useBirthTimeAutomaticJourneyEffects } from "@/hooks/use-birth-time-automatic-journey-effects";

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
  readonly selectOption: (optionId: string) => void;
  readonly submitUnmatchedContext: (note: string) => void;
  readonly finish: () => void;
  readonly retryQuestionGeneration: () => void;
};

export function useBirthTimeGuidedJourney(input: GuidedJourneyInput): BirthTimeGuidedController {
  const { journey, onJourney, onReady, onEditBirthTimeDetails, preview } = input;
  const latest = useRef(journey);
  const busy = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [pollRun, setPollRun] = useState(0);
  const [generationRun, setGenerationRun] = useState(0);

  useEffect(() => {
    latest.current = journey;
  }, [journey]);

  const operate = useCallback((operation: (
    turn: JourneyClientResponse,
    publishIntermediate: (turn: JourneyClientResponse) => void,
  ) => Promise<JourneyClientResponse>) => {
    const current = journey;
    if (!current) return;
    const release = claimMutation(busy);
    if (release === null) return;
    let expected = current;
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
      release();
      setPending(false);
    });
  }, [journey, onJourney]);

  const actionId = () => globalThis.crypto.randomUUID();
  const question = useBirthTimeAutomaticJourneyEffects({
    journey,
    latest,
    preview,
    pollRun,
    generationRun,
    onJourney,
    setError,
  });

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
  const selectOption = (optionId: string) => operate((turn) => {
    if (preview || turn.journeyProtocol !== "dynamic-choice-v2"
      || turn.nextAction.kind !== "ask_dynamic_choice") return Promise.resolve(turn);
    return answerDynamicBirthTimeChoice({
      caseId: turn.caseId,
      actionId: actionId(),
      turnVersion: turn.turnVersion,
      questionId: turn.nextAction.question.questionId,
      optionId,
    });
  });
  const submitUnmatchedContext = (note: string) => operate((turn) => {
    if (preview || turn.journeyProtocol !== "dynamic-choice-v2"
      || turn.nextAction.kind !== "clarify_unmatched_answer") return Promise.resolve(turn);
    return reframeUnmatchedBirthTimeAnswer({
      caseId: turn.caseId,
      actionId: actionId(),
      turnVersion: turn.turnVersion,
      questionId: turn.nextAction.questionId,
      note,
    });
  });
  const finish = () => operate((turn) => preview
    ? Promise.resolve(turn)
    : finishBirthTimeRectification(turn.caseId, actionId(), turn.turnVersion));
  const retryQuestionGeneration = () => {
    if (journey?.journeyProtocol !== "dynamic-choice-v2") return;
    if (journey.nextAction.kind !== "generate_dynamic_question"
      && journey.nextAction.kind !== "retry_question_generation") return;
    setError("");
    setGenerationRun((value) => value + 1);
  };

  const action = journey?.nextAction;
  return {
    question,
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
    selectOption,
    submitUnmatchedContext,
    finish,
    retryQuestionGeneration,
  };
}
