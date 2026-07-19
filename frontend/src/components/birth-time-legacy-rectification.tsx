"use client";

import { BirthTimeCandidateResult } from "@/components/birth-time-candidate-result";
import { BirthTimeEvidenceDraftCard } from "@/components/birth-time-evidence-draft-card";
import { BirthTimeGuideTurn } from "@/components/birth-time-guide-turn";
import type { BirthTimeGuidedController } from "@/hooks/use-birth-time-guided-journey";
import { assistantIntentCopy } from "@/lib/birth-time-intake-model";
import type { LegacyJourneyClientResponse } from "@/lib/birth-time-journey-response-schema";
import { guidedTurnIdentity } from "@/lib/birth-time-guided-turn-identity";
import type { NextAction } from "@/lib/birth-time-journey-turn";

type LegacyRectificationProps = {
  readonly journey: LegacyJourneyClientResponse;
  readonly controller: BirthTimeGuidedController;
  readonly externalError: string;
};

function actionHeading(action: NextAction): { readonly title: string; readonly badge: string } {
  switch (action.kind) {
    case "ask_baseline_evidence": return { title: "回想一条关键经历", badge: "基础证据" };
    case "ask_adaptive_evidence": return { title: "继续缩小候选范围", badge: "自适应校正" };
    case "review_evidence_draft": return { title: "确认经历草稿", badge: "待确认" };
    case "score_pending": return { title: "正在比较候选时间", badge: "评分中" };
    case "retry_scoring": return { title: "评分需要重试", badge: "可恢复" };
    case "present_low_result": return { title: "候选范围已保存", badge: "证据不足" };
    case "present_medium_result": return { title: "候选范围已形成", badge: "中等置信" };
    case "candidate_saved": return { title: "候选范围已保存", badge: "已保存" };
    case "request_candidate_confirmation": return { title: "确认候选时间", badge: "待确认" };
    case "ready": return { title: "排盘时间已更新", badge: "已完成" };
    case "paused": return { title: "校正已暂停", badge: "已保存" };
  }
}

export function BirthTimeLegacyRectification(props: LegacyRectificationProps) {
  const action = props.journey.nextAction;
  const heading = actionHeading(action);
  const asksQuestion = action.kind === "ask_baseline_evidence" || action.kind === "ask_adaptive_evidence";
  const showsCandidate = action.kind === "present_low_result"
    || action.kind === "present_medium_result"
    || action.kind === "candidate_saved"
    || action.kind === "request_candidate_confirmation"
    || action.kind === "ready";
  const error = props.controller.error || props.externalError;

  return (
    <section className="birth-time-rectification onboarding-card" aria-labelledby="birth-time-assessment-title">
      <div className="birth-time-assessment-heading">
        <div><span>出生时间评估</span><h2 id="birth-time-assessment-title">{heading.title}</h2></div>
        <span className="birth-time-status-badge">{heading.badge}</span>
      </div>
      <dl className="birth-time-range-summary">
        <div><dt>当前范围</dt><dd>{props.journey.snapshot.reportedRange.label}</dd></div>
        <div><dt>应用状态</dt><dd>{action.kind === "ready" ? `当前使用 ${action.activeTime}` : "尚未更新排盘时间"}</dd></div>
      </dl>
      <p className="birth-time-assistant-intent" role="status">{assistantIntentCopy(props.journey.snapshot.assistantIntent)}</p>
      {asksQuestion && (
        <BirthTimeGuideTurn
          key={guidedTurnIdentity(props.journey.turnVersion, action.question.questionId)}
          pending={props.controller.pending}
          progress={props.journey.progress}
          question={props.controller.question}
          onPause={props.controller.pause}
          onSkip={props.controller.skip}
          onSubmit={props.controller.submitMessage}
        />
      )}
      {action.kind === "review_evidence_draft" && props.journey.evidenceDraft && (
        <BirthTimeEvidenceDraftCard
          key={props.journey.evidenceDraft.draftId}
          draft={props.journey.evidenceDraft}
          pending={props.controller.pending}
          onConfirm={props.controller.confirmDraft}
          onSkip={props.controller.skip}
        />
      )}
      {action.kind === "score_pending" && <p className="birth-time-scoring-status" role="status">正在使用已确认的关键经历评分…</p>}
      {action.kind === "retry_scoring" && <button className="button-primary birth-time-guided-action" disabled={props.controller.pending} onClick={props.controller.retryScoring} type="button">重新评分</button>}
      {action.kind === "paused" && <button className="button-primary birth-time-guided-action" disabled={props.controller.pending} onClick={props.controller.resume} type="button">继续校正</button>}
      {showsCandidate ? (
        <BirthTimeCandidateResult
          controller={props.controller}
          error={error}
          journey={props.journey}
        />
      ) : null}
      {error && !showsCandidate ? <p className="form-error" role="alert">{error}</p> : null}
    </section>
  );
}
