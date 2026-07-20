"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  answerDynamicBirthTimeChoice,
  confirmDynamicBirthTimeCandidate,
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
  completeGuidedBirthTimeCandidate,
  confirmGuidedBirthTimeCandidate,
  reviseBirthTimeEvidenceDraft,
  saveGuidedBirthTimeCandidate,
} from "@/lib/birth-time-guided-client";
import { confirmReviewedBirthTimeDraft } from "@/lib/birth-time-guided-draft-confirmation";
import {
  claimMutation,
  createStableActionIdentityRegistry,
  publishCurrentJourney,
  runStableJourneyAction,
} from "@/lib/birth-time-guided-effect-coordinator";
import type { EvidenceDatePrecision } from "@/lib/birth-time-question-planner";
import { useBirthTimeAutomaticJourneyEffects } from "@/hooks/use-birth-time-automatic-journey-effects";
import { advanceDynamicBirthTimePreview } from "@/lib/birth-time-dynamic-preview";
import type { DynamicPreviewCommand } from "@/lib/birth-time-dynamic-preview";

type GuidedJourneyInput = {
  readonly journey: JourneyClientResponse | null;
  readonly preview: boolean;
  readonly onJourney: (journey: JourneyClientResponse) => void;
  readonly onReady: (journey: JourneyClientResponse) => void;
  readonly onCandidateComplete: (journey: JourneyClientResponse, time: string) => void;
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
  readonly completeCandidate: (time: string) => void;
  readonly retryScoring: () => void;
  readonly saveCandidate: (resultId: string) => void;
  readonly confirmCandidate: (resultId: string, time: string) => void;
  readonly selectOption: (optionId: string) => void;
  readonly submitUnmatchedContext: (note: string) => void;
  readonly finish: () => void;
  readonly retryQuestionGeneration: () => void;
};

function previewAction(turn: JourneyClientResponse, command: DynamicPreviewCommand) {
  return turn.journeyProtocol === "dynamic-choice-v2"
    ? advanceDynamicBirthTimePreview(turn, command)
    : turn;
}

export function useBirthTimeGuidedJourney(input: GuidedJourneyInput): BirthTimeGuidedController {
  const { journey, onJourney, onReady, onCandidateComplete, onEditBirthTimeDetails, preview } = input;
  const latest = useRef(journey);
  const busy = useRef(false);
  const [actionRegistry] = useState(() => createStableActionIdentityRegistry());
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

  const stableCommand = <T>(
    caseId: string,
    turnVersion: number,
    operation: string,
    payload: readonly string[],
    send: (actionId: string) => Promise<T>,
  ) => runStableJourneyAction(actionRegistry, {
    caseId,
    turnVersion,
    operation,
    payload,
  }, send);
  const stableAction = <T>(
    turn: JourneyClientResponse,
    operation: string,
    payload: readonly string[],
    send: (actionId: string) => Promise<T>,
  ) => stableCommand(turn.caseId, turn.turnVersion, operation, payload, send);
  const question = useBirthTimeAutomaticJourneyEffects({
    journey,
    latest,
    actionRegistry,
    preview,
    pollRun,
    generationRun,
    onJourney,
    setError,
  });

  const submitMessage = (message: string) => operate((turn) => {
    if (preview) return Promise.resolve(turn);
    return stableAction(turn, "draft_evidence", [message.trim()], (actionId) => (
      draftBirthTimeEvidence(turn.caseId, actionId, turn.turnVersion, message).then((value) => value.turn)
    ));
  });

  const confirmDraft = (precision: EvidenceDatePrecision, date: string) => operate(async (turn, publishIntermediate) => {
    if (preview) return turn;
    return confirmReviewedBirthTimeDraft({ turn, precision, date }, {
      revise: (command) => stableCommand(
        command.caseId, command.turnVersion, "revise_evidence_draft", [command.precision, command.date],
        (actionId) => reviseBirthTimeEvidenceDraft({ ...command, actionId }),
      ),
      publish: publishIntermediate,
      confirm: (command) => stableCommand(
        command.caseId, command.turnVersion, "confirm_evidence_draft", [command.draftId],
        (actionId) => confirmBirthTimeEvidenceDraft(
          command.caseId, actionId, command.turnVersion, command.draftId,
        ),
      ),
    });
  });

  const skip = () => operate((turn) => preview ? Promise.resolve(turn) : stableAction(
    turn, "skip_evidence_question", [],
    (actionId) => skipBirthTimeEvidenceQuestion(turn.caseId, actionId, turn.turnVersion),
  ));
  const pause = () => operate((turn) => preview ? Promise.resolve(previewAction(turn, { kind: "pause" })) : stableAction(
    turn, "pause_rectification", [],
    (actionId) => pauseBirthTimeRectification(turn.caseId, actionId, turn.turnVersion),
  ));
  const resume = () => operate((turn) => preview ? Promise.resolve(previewAction(turn, { kind: "resume" })) : resumeBirthTimeJourney(turn.caseId));
  const acknowledgeReady = () => {
    if (journey?.nextAction.kind === "ready") onReady(journey);
  };
  const completeCandidate = (time: string) => {
    const turn = journey;
    const resultId = turn?.candidateResult?.resultId;
    const winner = turn?.candidateResult?.winningSegment;
    if (!turn || !resultId || winner?.representativeTime !== time) return;
    if (turn.journeyProtocol === "dynamic-choice-v2") return;
    const release = claimMutation(busy);
    if (release === null) return;
    setPending(true);
    setError("");
    const completion = preview
      ? Promise.resolve()
      : completeGuidedBirthTimeCandidate({ caseId: turn.caseId, resultId, time });
    void completion
      .then(() => onCandidateComplete(turn, time))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "候选时间暂时无法保存"))
      .finally(() => {
        release();
        setPending(false);
      });
  };
  const retryScoring = () => {
    const turn = journey;
    if (preview && turn?.journeyProtocol === "dynamic-choice-v2"
      && (turn.nextAction.kind === "score_pending" || turn.nextAction.kind === "retry_scoring")) {
      operate((current) => Promise.resolve(previewAction(current, { kind: "retry_scoring" })));
      return;
    }
    if (turn?.nextAction.kind === "score_pending") {
      setError("");
      setPollRun((value) => value + 1);
      return;
    }
    operate((current) => current.nextAction.kind === "retry_scoring" && !preview
      ? pollBirthTimeScoring(current.caseId, current.nextAction.jobId)
      : Promise.resolve(current));
  };
  const saveCandidate = (resultId: string) => operate((turn) => preview ? Promise.resolve(turn) : stableAction(
    turn, "save_guided_candidate", [resultId],
    (actionId) => saveGuidedBirthTimeCandidate({ caseId: turn.caseId, actionId, turnVersion: turn.turnVersion, resultId }),
  ));
  const confirmCandidate = (resultId: string, time: string) => operate((turn) => preview ? Promise.resolve(turn) : stableAction(
    turn, turn.journeyProtocol === "dynamic-choice-v2" ? "confirm_dynamic_candidate" : "confirm_guided_candidate", [resultId, time],
    (actionId) => turn.journeyProtocol === "dynamic-choice-v2"
      ? confirmDynamicBirthTimeCandidate({ caseId: turn.caseId, actionId, turnVersion: turn.turnVersion, resultId, time })
      : confirmGuidedBirthTimeCandidate({ caseId: turn.caseId, actionId, turnVersion: turn.turnVersion, resultId, time }),
  ));
  const selectOption = (optionId: string) => operate((turn) => {
    if (turn.journeyProtocol !== "dynamic-choice-v2"
      || turn.nextAction.kind !== "ask_dynamic_choice") return Promise.resolve(turn);
    if (preview) return Promise.resolve(previewAction(turn, { kind: "select", optionId }));
    const questionId = turn.nextAction.question.questionId;
    return stableAction(turn, "answer_dynamic_choice", [questionId, optionId], (actionId) => (
      answerDynamicBirthTimeChoice({
        caseId: turn.caseId, actionId, turnVersion: turn.turnVersion, questionId, optionId,
      })
    ));
  });
  const submitUnmatchedContext = (note: string) => operate((turn) => {
    if (turn.journeyProtocol !== "dynamic-choice-v2"
      || turn.nextAction.kind !== "clarify_unmatched_answer") return Promise.resolve(turn);
    if (preview) return Promise.resolve(previewAction(turn, { kind: "reframe" }));
    const questionId = turn.nextAction.questionId;
    return stableAction(turn, "reframe_unmatched", [questionId, note.trim()], (actionId) => (
      reframeUnmatchedBirthTimeAnswer({
        caseId: turn.caseId, actionId, turnVersion: turn.turnVersion, questionId, note,
      })
    ));
  });
  const finish = () => operate((turn) => preview
    ? Promise.resolve(previewAction(turn, { kind: "finish" }))
    : stableAction(turn, "finish_rectification", [], (actionId) => (
      finishBirthTimeRectification(turn.caseId, actionId, turn.turnVersion)
    )));
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
    completeCandidate,
    retryScoring,
    saveCandidate,
    confirmCandidate,
    selectOption,
    submitUnmatchedContext,
    finish,
    retryQuestionGeneration,
  };
}
