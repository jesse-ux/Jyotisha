"use client";

import { ArrowUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useRectificationV4 } from "@/hooks/use-rectification-v4";
import type { ChatMessageView } from "@/lib/chat-message-view";
import type { PublicLanguageModel } from "@/lib/public-models";
import type { RectificationV4ApiResponse } from "@/lib/rectification-v4/contracts";
import { ChatMessageRow } from "./chat-message-row";
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

export function rectificationV4ChatMessages(
  data: RectificationV4ApiResponse | null,
  processing: boolean,
  pendingConsultationQuestion?: string | null,
): readonly ChatMessageView[] {
  if (!data) {
    return [{
      role: "assistant",
      text: "",
      renderKey: "rectification-loading",
      state: "thinking",
    }];
  }

  const messages: ChatMessageView[] = [];
  if (pendingConsultationQuestion?.trim()) {
    messages.push({
      role: "assistant",
      text: `我先陪你把出生时间范围核对清楚，之后再回到你原来的问题：“${pendingConsultationQuestion.trim()}”`,
      renderKey: "rectification-pending-consultation",
      state: "settled",
    });
  }

  for (const turn of data.turns) {
    messages.push({
      role: "assistant",
      text: turn.question,
      renderKey: `rectification-question-${turn.id}`,
      state: "settled",
    });
    if (turn.answer) {
      messages.push({
        role: "user",
        text: turn.answer,
        renderKey: `rectification-answer-${turn.id}`,
        state: "settled",
      });
    }
  }

  const caseValue = data.case;
  const primary = caseValue.latestSnapshot?.clusters[0];
  if (caseValue.acceptedRange) {
    messages.push({
      role: "assistant",
      text: `候选范围已保存为 ${caseValue.acceptedRange.start}–${caseValue.acceptedRange.end}。这是校正得到的候选范围，原出生时间没有被自动改写。`,
      renderKey: `rectification-accepted-${caseValue.version}`,
      state: "settled",
    });
  } else if (caseValue.status === "range_ready" && primary) {
    messages.push({
      role: "assistant",
      text: `根据目前这些经历，可以先把范围稳定缩小到 ${primary.startTime}–${primary.endTime}。这是候选范围，不是已确认的出生分钟；你可以保存它，也可以继续补充经历。`,
      renderKey: `rectification-range-${caseValue.version}`,
      state: "settled",
    });
  }

  if (!processing && caseValue.currentQuestion && !caseValue.acceptedRange) {
    messages.push({
      role: "assistant",
      text: caseValue.currentQuestion.prompt,
      renderKey: `rectification-current-${caseValue.currentQuestion.id}`,
      state: "settled",
    });
  }

  if (processing) {
    messages.push({
      role: "assistant",
      text: "",
      renderKey: `rectification-processing-${data.job?.id ?? caseValue.version}`,
      state: "thinking",
    });
  } else if (caseValue.status === "paused") {
    messages.push({
      role: "assistant",
      text: "进度已经保存。准备好后，我们可以从这里继续。",
      renderKey: `rectification-paused-${caseValue.version}`,
      state: "settled",
    });
  } else if (caseValue.status === "abandoned") {
    messages.push({
      role: "assistant",
      text: "这次校正已经结束，原出生时间没有被改写。",
      renderKey: `rectification-abandoned-${caseValue.version}`,
      state: "settled",
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
    <section className="rectification-chat" aria-label="生时校正对话" aria-busy={processing || controller.pending}>
      <div className="message-list" aria-live="polite">
        {messages.map((message) => <ChatMessageRow key={message.renderKey} message={message} />)}
        {controller.error && <p className="error-message" role="alert">{controller.error}</p>}
        <div ref={conversationEnd} />
      </div>

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
    </section>
  );
}
