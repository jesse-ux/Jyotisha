"use client";

import { useEffect, useRef } from "react";
import { BirthTimeCandidateResult } from "@/components/birth-time-candidate-result";
import {
  BirthTimeChoiceQuestion,
  BirthTimeQuestionProgress,
  BirthTimeUnmatchedClarification,
} from "@/components/birth-time-choice-question";
import { BirthTimeLegacyRectification } from "@/components/birth-time-legacy-rectification";
import type { BirthTimeGuidedController } from "@/hooks/use-birth-time-guided-journey";
import type { JourneyClientResponse } from "@/lib/birth-time-journey-client";
import type { DynamicNextAction } from "@/lib/birth-time-journey-turn-protocol";

type BirthTimeRectificationProps = {
  readonly journey: JourneyClientResponse;
  readonly controller: BirthTimeGuidedController;
  readonly externalError: string;
};

function dynamicHeading(action: DynamicNextAction): { readonly title: string; readonly badge: string } {
  switch (action.kind) {
    case "generate_dynamic_question": return { title: "准备下一道问题", badge: "正在生成" };
    case "retry_question_generation": return { title: "换一道问题", badge: "可重试" };
    case "ask_dynamic_choice": return { title: "选择更接近的情况", badge: "点击作答" };
    case "clarify_unmatched_answer": return { title: "换一道更合适的问题", badge: "可选补充" };
    case "score_pending": return { title: "正在缩小候选范围", badge: "评分中" };
    case "retry_scoring": return { title: "评分需要重试", badge: "可恢复" };
    case "present_low_result": return { title: "本次评估已结束", badge: "范围已保存" };
    case "present_medium_result": return { title: "候选范围已形成", badge: "评估已结束" };
    case "request_candidate_confirmation": return { title: "确认候选时间", badge: "待确认" };
    case "ready": return { title: "排盘时间已更新", badge: "已完成" };
    case "paused": return { title: "评估已暂停", badge: "进度已保存" };
  }
}

function statusCopy(action: DynamicNextAction): string {
  switch (action.kind) {
    case "generate_dynamic_question": return "系统正在根据当前候选范围准备更有区分度的问题。";
    case "retry_question_generation": return "这道问题暂时没有生成成功，可以原地重试。";
    case "ask_dynamic_choice": return "点击最接近的选项即可，不需要再填写日期或时间。";
    case "clarify_unmatched_answer": return "补充说明完全可选，也可以直接换一道题。";
    case "score_pending": return "正在应用刚才的选择，完成后会自动进入下一步。";
    case "retry_scoring": return "刚才的选择已经保存，可以安全重试同一评分任务。";
    case "present_low_result": return "目前没有足够的新信息继续稳定缩小范围，本次评估已结束并保存当前候选范围。";
    case "present_medium_result": return "已形成较窄的候选范围，本次评估已结束；它不会自动改动当前排盘时间。";
    case "request_candidate_confirmation": return "只有明确确认后，候选时间才会用于当前排盘。";
    case "ready": return `当前排盘使用时间已更新为 ${action.activeTime}。`;
    case "paused": return "当前问题和候选范围已保存，可以稍后从这里继续。";
  }
}

export function BirthTimeRectification(props: BirthTimeRectificationProps) {
  const assessmentHeadingRef = useRef<HTMLHeadingElement | null>(null);
  const previousTurnVersion = useRef(props.journey.turnVersion);
  useEffect(() => {
    const changed = previousTurnVersion.current !== props.journey.turnVersion;
    previousTurnVersion.current = props.journey.turnVersion;
    if (!changed || props.journey.journeyProtocol !== "dynamic-choice-v2") return;
    const action = props.journey.nextAction;
    if (action.kind !== "ask_dynamic_choice" && action.kind !== "clarify_unmatched_answer") {
      assessmentHeadingRef.current?.focus();
    }
  }, [props.journey]);
  if (props.journey.journeyProtocol !== "dynamic-choice-v2") {
    return <BirthTimeLegacyRectification {...props} journey={props.journey} />;
  }
  const action = props.journey.nextAction;
  const heading = dynamicHeading(action);
  const error = props.controller.error || props.externalError;
  const showsProgress = action.kind !== "ask_dynamic_choice" && action.kind !== "clarify_unmatched_answer";
  const showsCandidate = action.kind === "present_low_result"
    || action.kind === "present_medium_result"
    || action.kind === "request_candidate_confirmation"
    || action.kind === "ready";

  return (
    <section className="birth-time-rectification onboarding-card" aria-labelledby="birth-time-assessment-title">
      <div className="birth-time-assessment-heading">
        <div><span>出生时间评估</span><h2 id="birth-time-assessment-title" ref={assessmentHeadingRef} tabIndex={-1}>{heading.title}</h2></div>
        <span className="birth-time-status-badge">{heading.badge}</span>
      </div>
      {showsProgress && <BirthTimeQuestionProgress progress={props.journey.progress} />}
      <p className="birth-time-assistant-intent" role="status">{statusCopy(action)}</p>
      {action.kind === "ask_dynamic_choice" && (
        <BirthTimeChoiceQuestion
          key={`${props.journey.turnVersion}:${action.question.questionId}`}
          error={error}
          onFinish={props.controller.finish}
          onPause={props.controller.pause}
          onSelect={props.controller.selectOption}
          pending={props.controller.pending}
          progress={props.journey.progress}
          question={action.question}
        />
      )}
      {action.kind === "clarify_unmatched_answer" && (
        <BirthTimeUnmatchedClarification
          error={error}
          onFinish={props.controller.finish}
          onPause={props.controller.pause}
          onReframe={props.controller.submitUnmatchedContext}
          pending={props.controller.pending}
          progress={props.journey.progress}
        />
      )}
      {(action.kind === "generate_dynamic_question" || action.kind === "retry_question_generation") && error && (
        <button className="button-secondary birth-time-guided-action" disabled={props.controller.pending} onClick={props.controller.retryQuestionGeneration} type="button">重试当前问题</button>
      )}
      {action.kind === "score_pending" && (
        <div className="birth-time-scoring-status" aria-live="polite">
          <b>正在缩小候选范围…</b>
          {props.controller.pollRecoverable && <button className="button-secondary birth-time-guided-action" onClick={props.controller.retryScoring} type="button">重新检查评分状态</button>}
        </div>
      )}
      {action.kind === "retry_scoring" && <button className="button-primary birth-time-guided-action" disabled={props.controller.pending} onClick={props.controller.retryScoring} type="button">重新评分</button>}
      {action.kind === "paused" && <button className="button-primary birth-time-guided-action" disabled={props.controller.pending} onClick={props.controller.resume} type="button">继续本次评估</button>}
      {showsCandidate && <BirthTimeCandidateResult controller={props.controller} journey={props.journey} />}
      {error && action.kind !== "ask_dynamic_choice" && action.kind !== "clarify_unmatched_answer" && <p className="form-error" role="alert">{error}</p>}
    </section>
  );
}
