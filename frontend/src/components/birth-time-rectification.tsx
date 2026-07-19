"use client";

import { BirthTimeCandidateResult } from "@/components/birth-time-candidate-result";
import { BirthTimeEvidenceDraftCard } from "@/components/birth-time-evidence-draft-card";
import { BirthTimeGuideTurn } from "@/components/birth-time-guide-turn";
import type { BirthTimeGuidedController } from "@/hooks/use-birth-time-guided-journey";
import { assistantIntentCopy } from "@/lib/birth-time-intake-model";
import type { JourneyClientResponse } from "@/lib/birth-time-journey-client";
import { guidedTurnIdentity } from "@/lib/birth-time-guided-turn-identity";
import type { NextAction } from "@/lib/birth-time-journey-turn";
import type { DynamicNextAction } from "@/lib/birth-time-journey-turn-protocol";

type BirthTimeRectificationProps = {
  readonly journey: JourneyClientResponse;
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
    default: {
      const exhaustive: never = action;
      return exhaustive;
    }
  }
}

function dynamicStatus(action: DynamicNextAction): string {
  switch (action.kind) {
    case "generate_dynamic_question": return "正在准备下一道候选区分问题…";
    case "retry_question_generation": return "问题暂时未能生成，可以重试当前步骤。";
    case "ask_dynamic_choice": return action.question.prompt;
    case "clarify_unmatched_answer": return "可以补充一句，再换一道更合适的问题。";
    case "score_pending": return "正在根据刚才的选择缩小候选范围…";
    case "retry_scoring": return "评分暂时未完成，可以重试同一任务。";
    case "present_low_result": return "本次评估已结束并保存当前候选范围。";
    case "present_medium_result": return "已形成较窄候选范围，本次评估已结束。";
    case "request_candidate_confirmation": return "请确认是否使用当前候选时间。";
    case "ready": return `当前排盘使用时间已更新为 ${action.activeTime}。`;
    case "paused": return "当前问题和候选范围已保存。";
    default: {
      const exhaustive: never = action;
      return exhaustive;
    }
  }
}

export function BirthTimeRectification(props: BirthTimeRectificationProps) {
  if (props.journey.journeyProtocol === "dynamic-choice-v2") {
    const generationFailed = Boolean(props.controller.error || props.externalError)
      && (props.journey.nextAction.kind === "generate_dynamic_question"
        || props.journey.nextAction.kind === "retry_question_generation");
    return (
      <section className="birth-time-rectification onboarding-card" aria-labelledby="birth-time-assessment-title">
        <div className="birth-time-assessment-heading">
          <div><span>出生时间评估</span><h2 id="birth-time-assessment-title">动态候选评估</h2></div>
          <span className="birth-time-status-badge">动态评估</span>
        </div>
        <p className="birth-time-assistant-intent" role="status">{dynamicStatus(props.journey.nextAction)}</p>
        {generationFailed && <button className="button-secondary birth-time-guided-action" type="button" onClick={props.controller.retryQuestionGeneration}>重试当前问题</button>}
        {(props.controller.error || props.externalError) && <p className="form-error" role="alert">{props.controller.error || props.externalError}</p>}
      </section>
    );
  }
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
      {action.kind === "score_pending" && (
        <div className="birth-time-scoring-status" aria-live="polite">
          <b>正在使用已确认的关键经历评分</b>
          <p>完成后会自动显示下一题或候选结果，无需再点击比较按钮。</p>
          {props.controller.pollRecoverable && <button className="button-secondary birth-time-guided-action" type="button" onClick={props.controller.retryScoring}>重新检查评分状态</button>}
        </div>
      )}
      {action.kind === "retry_scoring" && (
        <div className="birth-time-scoring-status" role="status">
          <p>已确认的关键经历仍然安全保存，可以<span className="phrase-nowrap">重试</span>同一评分任务。</p>
          <button className="button-primary birth-time-guided-action" disabled={props.controller.pending} type="button" onClick={props.controller.retryScoring}>重新评分</button>
        </div>
      )}
      {action.kind === "paused" && (
        <div className="birth-time-candidate-terminal" role="status">
          <p>当前问题和证据已保存，可以现在继续，也可以稍后回来。</p>
          <button className="button-primary birth-time-guided-action" disabled={props.controller.pending} type="button" onClick={props.controller.resume}>继续校正</button>
        </div>
      )}
      {showsCandidate && <BirthTimeCandidateResult controller={props.controller} journey={props.journey} />}
      {error && <p className="form-error" role="alert">{error}</p>}
    </section>
  );
}
