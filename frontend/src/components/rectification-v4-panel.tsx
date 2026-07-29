"use client";

import { ArrowUp, Check, Copy, RotateCcw, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AgentActivityStatus } from "@/components/agent-activity-status";
import { useRectificationV4 } from "@/hooks/use-rectification-v4";
import type { ChatMessageView } from "@/lib/chat-message-view";
import type { PublicLanguageModel } from "@/lib/public-models";
import type { RectificationAnalysisItem, RectificationAnalysisTrace, RectificationV4ApiResponse } from "@/lib/rectification-v4/contracts";
import { AgentAvatar, ChatMessageRow } from "./chat-message-row";
import { ModelSelector } from "./model-selector";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";

export type RectificationV4Continuation = Readonly<{
  protocol: "rectification-evidence-v4";
  question: string;
  caseId: string;
  caseVersion: number;
  acceptedRange: Readonly<{ start: string; end: string }>;
}>;

type RectificationV4PanelProps = Readonly<{
  models: readonly PublicLanguageModel[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onPendingChange?: (pending: boolean) => void;
  onContinueOriginalQuestion?: (continuation: RectificationV4Continuation) => void;
}>;

type RectificationChatMessageView = ChatMessageView & Readonly<{
  analysisTrace?: RectificationAnalysisTrace;
}>;

const phaseLabels = {
  collecting_evidence: "正在准备继续收集经历…",
  extracting_evidence: "正在整理你刚才提到的经历…",
  scoring_candidates: "正在扫描候选时间…",
  checking_robustness: "正在检查候选范围的稳定性…",
  planning_question: "正在生成语义问题机会…",
  reasoning: "正在选择下一步动作…",
  rendering: "正在生成安全回复…",
  complete: "分析已完成",
} as const;

export function rectificationPhaseLabel(
  phase: NonNullable<RectificationV4ApiResponse["job"]>["phase"],
): string {
  return phaseLabels[phase];
}

function durationLabel(durationMs: number | null): string | null {
  if (durationMs === null || durationMs < 0) return null;
  return durationMs < 1_000 ? `${durationMs} 毫秒` : `${(durationMs / 1_000).toFixed(1)} 秒`;
}

function publicStatusLabel(status: string): string {
  return ({
    completed: "已完成",
    succeeded: "已完成",
    running: "进行中",
    failed: "未完成",
    skipped: "已跳过",
    legacy: "历史记录",
  } as Record<string, string>)[status] ?? "已记录";
}

function RectificationAnalysisDetails({ trace }: Readonly<{ trace: RectificationAnalysisTrace }>) {
  return (
    <details className="rectification-analysis">
      <summary>
        <span>分析过程</span>
        <small>{publicStatusLabel(trace.status)}</small>
      </summary>
      <div className="rectification-analysis-content">
        {trace.stages.length > 0 && (
          <section aria-label="执行阶段">
            <h4>执行阶段</h4>
            <ol>
              {trace.stages.map((stage, index) => {
                const duration = durationLabel(stage.durationMs);
                return (
                  <li key={`${stage.phase}-${index}`}>
                    <span>{stage.label}</span>
                    <small>{publicStatusLabel(stage.status)}{duration ? ` · ${duration}` : ""}</small>
                  </li>
                );
              })}
            </ol>
          </section>
        )}
        {trace.toolCalls.length > 0 && (
          <section aria-label="实际调用">
            <h4>实际调用</h4>
            <ul>
              {trace.toolCalls.map((toolCall, index) => {
                const duration = durationLabel(toolCall.durationMs);
                return (
                  <li key={`${toolCall.category}-${index}`}>
                    <span>{toolCall.label}</span>
                    <small>{publicStatusLabel(toolCall.outcome)}{duration ? ` · ${duration}` : ""}</small>
                  </li>
                );
              })}
            </ul>
          </section>
        )}
        {trace.techniques.length > 0 && (
          <section aria-label="实际使用的技法">
            <h4>实际使用的技法</h4>
            <p>{trace.techniques.join("、")}</p>
          </section>
        )}
        {trace.reasoningSource === "provider_summary" && trace.reasoningSummary && (
          <section aria-label="推理摘要">
            <h4>推理摘要</h4>
            <p>{trace.reasoningSummary}</p>
          </section>
        )}
      </div>
    </details>
  );
}

function RectificationMessageRow({ message }: Readonly<{ message: RectificationChatMessageView }>) {
  if (message.state !== "thinking" || !message.text) return <ChatMessageRow message={message} />;

  return (
    <article className="message message-assistant" aria-label="Jyotisha 正在分析">
      <AgentAvatar />
      <div className="message-content">
        <div className="message-bubble">
          <AgentActivityStatus state="working" label={message.text} />
        </div>
      </div>
    </article>
  );
}

export function toggleRectificationFeedback(
  current: "up" | "down" | undefined,
  requested: "up" | "down",
): "up" | "down" | undefined {
  return current === requested ? undefined : requested;
}

export function canRegenerateRectificationMessage(input: Readonly<{
  message: ChatMessageView;
  currentMessageKey: string | null;
  deploymentMode: RectificationV4ApiResponse["case"]["deploymentMode"] | null;
  busy: boolean;
  canAnswer: boolean;
}>): boolean {
  return input.deploymentMode === "v5_agent"
    && input.message.role === "assistant"
    && input.message.state === "settled"
    && input.message.renderKey === input.currentMessageKey
    && !input.busy
    && input.canAnswer;
}

export function rectificationV4ChatMessages(
  data: RectificationV4ApiResponse | null,
  processing: boolean,
  pendingConsultationQuestion?: string | null,
): readonly RectificationChatMessageView[] {
  if (!data) {
    return [{
      role: "assistant",
      text: "",
      renderKey: "rectification-loading",
      state: "thinking",
    }];
  }

  const messages: RectificationChatMessageView[] = [];
  const analysis = data.case.deploymentMode === "v5_agent"
    ? (data as RectificationV4ApiResponse & {
      readonly analysis?: readonly RectificationAnalysisItem[];
    }).analysis ?? []
    : [];
  const analysisBySourceTurnId = new Map(analysis.map((item) => [item.sourceTurnId, item.trace]));
  if (pendingConsultationQuestion?.trim()) {
    messages.push({
      role: "assistant",
      text: `我先陪你把出生时间范围核对清楚，之后再回到你原来的问题：“${pendingConsultationQuestion.trim()}”`,
      renderKey: "rectification-pending-consultation",
      state: "settled",
    });
  }

  let previousTurnId: string | null = null;
  for (const turn of data.turns) {
    messages.push({
      role: "assistant",
      text: turn.question,
      renderKey: `rectification-question-${turn.id}`,
      state: "settled",
      analysisTrace: previousTurnId ? analysisBySourceTurnId.get(previousTurnId) : undefined,
    });
    if (turn.answer) {
      messages.push({
        role: "user",
        text: turn.answer,
        renderKey: `rectification-answer-${turn.id}`,
        state: "settled",
      });
    }
    previousTurnId = turn.id;
  }

  const caseValue = data.case;
  const primary = caseValue.latestSnapshot?.clusters[0];
  const latestTurnTrace = analysisBySourceTurnId.get(data.turns.at(-1)?.id ?? "");
  const terminalTrace = caseValue.currentQuestion ? undefined : latestTurnTrace;
  if (caseValue.acceptedRange) {
    messages.push({
      role: "assistant",
      text: `候选范围已保存为 ${caseValue.acceptedRange.start}–${caseValue.acceptedRange.end}。这是校正得到的候选范围，原出生时间没有被自动改写。`,
      renderKey: `rectification-accepted-${caseValue.version}`,
      state: "settled",
      analysisTrace: terminalTrace,
    });
  } else if (caseValue.status === "range_ready" && primary) {
    messages.push({
      role: "assistant",
      text: `根据目前这些经历，可以先把范围稳定缩小到 ${primary.startTime}–${primary.endTime}。这是候选范围，不是已确认的出生分钟；你可以保存它，也可以继续补充经历。`,
      renderKey: `rectification-range-${caseValue.version}`,
      state: "settled",
      analysisTrace: terminalTrace,
    });
  }

  if (!processing && caseValue.currentQuestion && !caseValue.acceptedRange) {
    messages.push({
      role: "assistant",
      text: caseValue.currentQuestion.prompt,
      renderKey: `rectification-current-${caseValue.currentQuestion.id}`,
      state: "settled",
      analysisTrace: latestTurnTrace,
    });
  }

  if (processing) {
    messages.push({
      role: "assistant",
      text: rectificationPhaseLabel(data.job?.phase ?? caseValue.phase),
      renderKey: `rectification-processing-${data.job?.id ?? caseValue.version}`,
      state: "thinking",
    });
  } else if (caseValue.status === "paused") {
    messages.push({
      role: "assistant",
      text: "进度已经保存。准备好后，我们可以从这里继续。",
      renderKey: `rectification-paused-${caseValue.version}`,
      state: "settled",
      analysisTrace: terminalTrace,
    });
  } else if (caseValue.status === "abandoned") {
    messages.push({
      role: "assistant",
      text: "这次校正已经结束，原出生时间没有被改写。",
      renderKey: `rectification-abandoned-${caseValue.version}`,
      state: "settled",
      analysisTrace: terminalTrace,
    });
  }

  return messages;
}

export function RectificationV4Panel(props: RectificationV4PanelProps) {
  const controller = useRectificationV4({
    pendingConsultationQuestion: props.pendingConsultationQuestion,
    onPendingChange: props.onPendingChange,
  });
  const [draft, setDraft] = useState("");
  const [feedback, setFeedback] = useState<Record<string, "up" | "down" | undefined>>({});
  const [copiedMessageKey, setCopiedMessageKey] = useState<string | null>(null);
  const [regeneratingMessageKey, setRegeneratingMessageKey] = useState<string | null>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const conversationEnd = useRef<HTMLDivElement>(null);
  const caseValue = controller.data?.case;
  const processing = Boolean(caseValue && (
    caseValue.status === "processing"
    || ["pending", "processing"].includes(controller.job?.status ?? "")
  ));
  const messages = rectificationV4ChatMessages(
    controller.data,
    processing,
    props.pendingConsultationQuestion,
  );
  const canAnswer = Boolean(caseValue?.currentQuestion)
    && !processing
    && !controller.pending
    && ["awaiting_answer", "range_ready"].includes(caseValue?.status ?? "");
  const currentMessageKey = caseValue?.currentQuestion
    ? `rectification-current-${caseValue.currentQuestion.id}`
    : null;
  const busy = processing || controller.pending || regeneratingMessageKey !== null;
  const canAcceptRange = caseValue?.status === "range_ready"
    && Boolean(caseValue.latestSnapshot?.canAcceptRange)
    && !caseValue.acceptedRange;
  const handoff = controller.handoff;
  const canContinue = Boolean(
    caseValue?.acceptedRange
    && handoff?.status === "pending"
    && props.onContinueOriginalQuestion,
  );
  const showControls = Boolean(caseValue && caseValue.status !== "abandoned" && (
    canAnswer || canAcceptRange || canContinue || caseValue.status === "paused"
  ));

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    conversationEnd.current?.scrollIntoView({
      behavior: processing || controller.pending || reduceMotion ? "auto" : "smooth",
      block: "end",
    });
  }, [controller.error, controller.pending, messages.length, processing]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const answer = draft.trim();
    if (!answer || !canAnswer) return;
    const result = await controller.answer(answer, props.selectedModelId || null);
    if (result) setDraft("");
  }

  async function copyMessage(message: ChatMessageView) {
    try {
      await navigator.clipboard.writeText(message.text);
      setCopiedMessageKey(message.renderKey);
      window.setTimeout(() => setCopiedMessageKey((current) => (
        current === message.renderKey ? null : current
      )), 1_500);
    } catch {
      // Clipboard permission failures must not interrupt the conversation.
    }
  }

  async function regenerateMessage(messageKey: string) {
    setRegeneratingMessageKey(messageKey);
    try {
      await controller.regenerate();
    } finally {
      setRegeneratingMessageKey((current) => current === messageKey ? null : current);
    }
  }

  function continueOriginalQuestion() {
    if (!caseValue?.acceptedRange || !handoff) return;
    props.onContinueOriginalQuestion?.({
      protocol: "rectification-evidence-v4",
      question: handoff.question,
      caseId: caseValue.id,
      caseVersion: caseValue.version,
      acceptedRange: caseValue.acceptedRange,
    });
  }

  return (
    <>
      <section className="conversation" aria-label="生时校正对话" aria-busy={processing || controller.pending}>
        <div className="message-list" aria-live="polite">
          {messages.map((message) => {
            const showActions = caseValue?.deploymentMode === "v5_agent"
              && message.role === "assistant"
              && message.state === "settled"
              && Boolean(message.text);
            const regenerating = regeneratingMessageKey === message.renderKey;
            const canRegenerate = canRegenerateRectificationMessage({
              message,
              currentMessageKey,
              deploymentMode: caseValue?.deploymentMode ?? null,
              busy,
              canAnswer,
            });
            return (
              <div className="rectification-message-entry" key={message.renderKey}>
                {message.role === "assistant" && message.state === "settled" && message.analysisTrace && (
                  <RectificationAnalysisDetails trace={message.analysisTrace} />
                )}
                <RectificationMessageRow message={regenerating
                  ? { ...message, text: "", state: "thinking" }
                  : message} />
                {showActions && !regenerating && (
                  <div className="rectification-message-actions" aria-label="Agent 回答操作">
                    <button
                      aria-label="赞"
                      aria-pressed={feedback[message.renderKey] === "up"}
                      className={feedback[message.renderKey] === "up" ? "is-active" : ""}
                      title="赞"
                      type="button"
                      onClick={() => setFeedback((current) => ({
                        ...current,
                        [message.renderKey]: toggleRectificationFeedback(current[message.renderKey], "up"),
                      }))}
                    >
                      <ThumbsUp aria-hidden="true" />
                    </button>
                    <button
                      aria-label="踩"
                      aria-pressed={feedback[message.renderKey] === "down"}
                      className={feedback[message.renderKey] === "down" ? "is-active" : ""}
                      title="踩"
                      type="button"
                      onClick={() => setFeedback((current) => ({
                        ...current,
                        [message.renderKey]: toggleRectificationFeedback(current[message.renderKey], "down"),
                      }))}
                    >
                      <ThumbsDown aria-hidden="true" />
                    </button>
                    <button aria-label="复制回答" title="复制" type="button" onClick={() => void copyMessage(message)}>
                      {copiedMessageKey === message.renderKey
                        ? <Check aria-hidden="true" />
                        : <Copy aria-hidden="true" />}
                    </button>
                    <button
                      aria-label="重新生成回答"
                      disabled={!canRegenerate}
                      title={canRegenerate ? "重新生成" : "只能重新生成当前问题"}
                      type="button"
                      onClick={() => void regenerateMessage(message.renderKey)}
                    >
                      <RotateCcw aria-hidden="true" />
                    </button>
                  </div>
                )}
              </div>
            );
          })}
          {controller.error && <p className="error-message" role="alert">{controller.error}</p>}
          <div ref={conversationEnd} />
        </div>
      </section>

      {showControls && (
        <div className="composer-wrap">
          {(canAcceptRange || canContinue || caseValue?.status === "paused") && (
            <div className="composer-suggestions" aria-label="生时校正操作">
              {canAcceptRange && (
                <button type="button" disabled={controller.pending} onClick={() => void controller.acceptRange()}>
                  保存这个候选范围
                </button>
              )}
              {canContinue && (
                <button type="button" disabled={props.continuationPending} onClick={continueOriginalQuestion}>
                  {props.continuationPending ? "正在回到原问题…" : "带着候选范围继续原问题"}
                </button>
              )}
              {caseValue?.status === "paused" && (
                <button type="button" disabled={controller.pending} onClick={() => void controller.resume()}>
                  继续校正
                </button>
              )}
            </div>
          )}

          {canAnswer && (
            <form className="composer" onSubmit={submit}>
              <Textarea
                ref={composer}
                aria-label="继续描述你的经历"
                value={draft}
                disabled={controller.pending}
                placeholder="继续说你记得的人生经历…"
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                    event.preventDefault();
                    event.currentTarget.form?.requestSubmit();
                  }
                }}
              />
              <Button aria-label="发送" disabled={!draft.trim() || controller.pending} size="icon" type="submit">
                <ArrowUp aria-hidden="true" />
              </Button>
            </form>
          )}

          <div className="composer-footer">
            <ModelSelector
              models={props.models}
              selectedModelId={props.selectedModelId}
              disabled={controller.pending || processing}
              onSelect={props.onSelectModel}
            />
          </div>
        </div>
      )}
    </>
  );
}
