"use client";

import { useState } from "react";
import {
  choiceQuestionGroups,
  choiceSelectionIntent,
  normalizeUnmatchedNote,
  rangeLabel,
} from "@/lib/birth-time-choice-question-model";
import type {
  DynamicJourneyProgress,
  PublicDynamicChoiceQuestion,
} from "@/lib/birth-time-journey-turn-protocol";

type SharedQuestionProps = {
  readonly progress: DynamicJourneyProgress;
  readonly pending: boolean;
  readonly error: string;
  readonly onPause: () => void;
  readonly onFinish: () => void;
};

type ChoiceQuestionProps = SharedQuestionProps & {
  readonly question: PublicDynamicChoiceQuestion;
  readonly onSelect: (optionId: string) => void;
};

type ClarificationProps = SharedQuestionProps & {
  readonly onReframe: (note: string) => void;
};

export function BirthTimeQuestionProgress({ progress }: {
  readonly progress: DynamicJourneyProgress;
}) {
  return (
    <div className="birth-time-question-progress">
      <b>已完成 {progress.effectiveAnswerCount} 个有效判断</b>
      <span>当前候选范围：{rangeLabel(progress.currentRange)}</span>
    </div>
  );
}

export function BirthTimeChoiceQuestion(props: ChoiceQuestionProps) {
  const groups = choiceQuestionGroups(props.question);
  const [selectedId, setSelectedId] = useState("");
  const select = (option: PublicDynamicChoiceQuestion["options"][number]) => {
    const intent = choiceSelectionIntent(option);
    setSelectedId(intent.optionId);
    props.onSelect(intent.optionId);
  };

  return (
    <div className="birth-time-choice-surface" aria-busy={props.pending}>
      <BirthTimeQuestionProgress progress={props.progress} />
      <fieldset className="birth-time-choice-question" disabled={props.pending}>
        <legend>{props.question.prompt}</legend>
        <div className="birth-time-primary-choices">
          {groups.primary.map((option) => (
            <button
              className="birth-time-choice-option is-primary"
              data-selected={selectedId === option.optionId}
              key={option.optionId}
              onClick={() => select(option)}
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="birth-time-special-choices">
          {[groups.unknown, groups.unmatched].map((option) => (
            <button
              className="birth-time-choice-option is-secondary"
              data-selected={selectedId === option.optionId}
              key={option.optionId}
              onClick={() => select(option)}
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>
      </fieldset>
      {props.pending && <p className="birth-time-choice-pending" role="status">正在缩小候选范围…</p>}
      <JourneyControls {...props} />
    </div>
  );
}

export function BirthTimeUnmatchedClarification(props: ClarificationProps) {
  const [note, setNote] = useState("");
  return (
    <div className="birth-time-choice-surface" aria-busy={props.pending}>
      <BirthTimeQuestionProgress progress={props.progress} />
      <fieldset className="birth-time-choice-question" disabled={props.pending}>
        <legend>这道题都不符合你的情况吗？</legend>
        <label className="birth-time-unmatched-note">
          <span>补充一句（可选）</span>
          <textarea
            maxLength={240}
            onChange={(event) => setNote(event.target.value)}
            placeholder="例如：这段变化发生得更早，或情况不太一样"
            value={note}
          />
        </label>
        <div className="birth-time-reframe-actions">
          <button className="button-secondary birth-time-guided-action" onClick={() => props.onReframe("")} type="button">换一道题</button>
          <button className="button-primary birth-time-guided-action" onClick={() => props.onReframe(normalizeUnmatchedNote(note))} type="button">提交补充并换题</button>
        </div>
      </fieldset>
      {props.pending && <p className="birth-time-choice-pending" role="status">正在换一道更合适的问题…</p>}
      <JourneyControls {...props} />
    </div>
  );
}

function JourneyControls(props: SharedQuestionProps) {
  return (
    <>
      <div className="birth-time-journey-controls">
        <button className="button-text birth-time-guided-action" disabled={props.pending} onClick={props.onPause} type="button">暂停，稍后继续</button>
        <button className="button-text birth-time-guided-action" disabled={props.pending} onClick={props.onFinish} type="button">结束并保存当前范围</button>
      </div>
      {props.error && <p className="form-error" role="alert">{props.error}</p>}
    </>
  );
}
