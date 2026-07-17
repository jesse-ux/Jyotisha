"use client";

import { assistantIntentCopy } from "@/lib/birth-time-intake-model";
import type {
  JourneyAnswer,
  JourneyClientResponse,
} from "@/lib/birth-time-journey-client";

type BirthTimeRectificationProps = {
  readonly journey: JourneyClientResponse;
  readonly answers: Readonly<Record<string, JourneyAnswer>>;
  readonly pendingQuestionId: string;
  readonly error: string;
  readonly onAnswer: (questionId: string, answer: JourneyAnswer) => void;
};

const fallbackOptions = [
  { key: "A", label: "明确有，而且时间大致吻合" },
  { key: "B", label: "有类似经历，但时间或程度不完全确定" },
  { key: "C", label: "没有明显发生" },
  { key: "D", label: "不确定 / 不记得" },
] as const;

export function BirthTimeRectification({
  journey,
  answers,
  pendingQuestionId,
  error,
  onAnswer,
}: BirthTimeRectificationProps) {
  const questions = journey.questionnaire?.questions.slice(0, 3) ?? [];
  const answeredCount = Object.keys(answers).length;

  return (
    <section className="birth-time-rectification onboarding-card" aria-labelledby="birth-time-assessment-title">
      <div className="birth-time-assessment-heading">
        <div>
          <span>出生时间评估</span>
          <h2 id="birth-time-assessment-title">
            {journey.snapshot.state === "candidate" ? "候选范围已保存" : "需要先缩小时间范围"}
          </h2>
        </div>
        <span className="birth-time-status-badge">
          {journey.snapshot.state === "candidate" ? "候选" : "校正中"}
        </span>
      </div>

      <dl className="birth-time-range-summary">
        <div><dt>当前范围</dt><dd>{journey.snapshot.reportedRange.label}</dd></div>
        <div><dt>应用状态</dt><dd>尚未设为排盘时间</dd></div>
      </dl>

      <p className="birth-time-assistant-intent" role="status">
        {assistantIntentCopy(journey.snapshot.assistantIntent)}
      </p>

      {questions.length > 0 ? (
        <div className="birth-time-question-list">
          <div className="birth-time-question-progress">
            <b>首轮问题</b>
            <span>{Math.min(answeredCount, questions.length)} / {questions.length}</span>
          </div>
          {questions.map((question, index) => (
            <fieldset className="birth-time-question" key={question.id}>
              <legend><span>{index + 1}</span>{question.prompt}</legend>
              <div className="birth-time-answer-list">
                {(question.options?.length ? question.options : fallbackOptions).map((option) => (
                  <button
                    aria-pressed={answers[question.id] === option.key}
                    className={answers[question.id] === option.key ? "is-selected" : ""}
                    disabled={Boolean(pendingQuestionId)}
                    key={option.key}
                    type="button"
                    onClick={() => onAnswer(question.id, option.key)}
                  >
                    <span>{option.key}</span>{option.label}
                  </button>
                ))}
              </div>
              {pendingQuestionId === question.id && <small role="status">正在更新候选范围…</small>}
            </fieldset>
          ))}
        </div>
      ) : (
        <p className="birth-time-assessment-unavailable">
          当前资料已经保留，但候选扫描暂时不可用。系统不会把未经验证的分钟用于正式排盘。
        </p>
      )}

      {error && <p className="form-error" role="alert">{error}</p>}
    </section>
  );
}
