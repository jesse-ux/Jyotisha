"use client";

import { useState } from "react";
import type { JourneyProgress } from "@/lib/birth-time-journey-turn";
import { protectOnboardingPhrases } from "@/lib/onboarding-copy";

type BirthTimeGuideTurnProps = {
  readonly question: string;
  readonly progress: JourneyProgress;
  readonly pending: boolean;
  readonly onSubmit: (message: string) => void;
  readonly onSkip: () => void;
  readonly onPause: () => void;
};

export function BirthTimeGuideTurn(props: BirthTimeGuideTurnProps) {
  const [message, setMessage] = useState("");
  const phase = props.progress.adaptiveRound > 0
    ? `自适应第 ${props.progress.adaptiveRound} / ${props.progress.maxAdaptiveRounds} 轮`
    : "基础证据";

  return (
    <div className="birth-time-guide-turn" aria-live="polite">
      <div className="birth-time-question-progress">
        <b>{phase}</b>
        <span>已确认 {props.progress.confirmedEvidenceCount} 条 / {props.progress.baselineDomainCount} 个领域</span>
      </div>
      <p className="birth-time-guide-question">{protectOnboardingPhrases(props.question)}</p>
      <label className="birth-time-guide-composer">
        <span>说说这段经历</span>
        <textarea
          aria-describedby="birth-time-guide-hint"
          disabled={props.pending}
          maxLength={500}
          rows={3}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && message.trim()) {
              event.preventDefault();
              props.onSubmit(message.trim());
            }
          }}
        />
      </label>
      <p id="birth-time-guide-hint" className="birth-time-guide-hint">说出大概年份也可以，不需要为了校正而猜测。</p>
      <div className="birth-time-guided-actions">
        <button className="button-text birth-time-guided-action" disabled={props.pending} type="button" onClick={props.onPause}>暂停，稍后继续</button>
        <button className="button-secondary birth-time-guided-action" disabled={props.pending} type="button" onClick={props.onSkip}>不记得，跳过</button>
        <button className="button-primary birth-time-guided-action" disabled={props.pending || !message.trim()} type="button" onClick={() => props.onSubmit(message.trim())}>
          {props.pending ? "整理中…" : "整理为经历草稿"}
        </button>
      </div>
    </div>
  );
}
