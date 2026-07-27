"use client";

import { ArrowUp, Check, Copy, RotateCcw, Square, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { ChatMessageRow } from "./chat-message-row.tsx";
import { AppLoadingIndicator } from "./app-loading-indicator.tsx";
import { ModelSelector } from "./model-selector.tsx";
import { Button } from "./ui/button.tsx";
import { Textarea } from "./ui/textarea.tsx";
import {
  RectificationV4Panel,
  type RectificationV4Continuation,
} from "./rectification-v4-panel.tsx";
import {
  type ConversationalRectificationMessage,
  type ConversationalRectificationStoredMessage,
  type ConversationalRectificationController,
} from "../hooks/use-conversational-rectification.ts";
import type { ConversationalRectificationTurn } from "../lib/conversational-rectification/contracts.ts";
import type { PublicLanguageModel } from "../lib/public-models.ts";

type SurfaceProps = Readonly<{
  controller: ConversationalRectificationController;
  openingAssistantText?: string;
  models: readonly PublicLanguageModel[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onContinueOriginalQuestion?: (question: string) => void;
}>;

const ANSWER_UNDO_WINDOW_MS = 2_500;

function safely(request: Promise<unknown>) {
  void request.catch(() => undefined);
}

export function ConversationalRectificationSurface({
  controller,
  openingAssistantText = "",
  models,
  selectedModelId,
  onSelectModel,
  pendingConsultationQuestion,
  continuationPending = false,
  onContinueOriginalQuestion,
}: SurfaceProps) {
  const composer = useRef<HTMLTextAreaElement>(null);
  const conversationEnd = useRef<HTMLDivElement>(null);
  const [feedback, setFeedback] = useState<Record<string, "up" | "down" | undefined>>({});
  const [copiedMessageKey, setCopiedMessageKey] = useState<string | null>(null);
  const [regeneratingMessageKey, setRegeneratingMessageKey] = useState<string | null>(null);
  const undoTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [submission, setSubmission] = useState<Readonly<{
    text: string;
    phase: "undo" | "generating";
    turnVersion: number;
  }> | null>(null);
  const turn = controller.turn;
  const messageCount = controller.messages?.length ?? 0;
  const latestMessageText = controller.messages?.[messageCount - 1]?.text ?? turn?.narrative ?? "";
  const latestAssistantKey = [...(controller.messages ?? [])]
    .reverse()
    .find((message) => message.role === "assistant")?.renderKey
    ?? `assistant-${turn?.turnVersion ?? 0}`;
  useEffect(() => () => {
    if (undoTimer.current) clearTimeout(undoTimer.current);
  }, []);
  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    conversationEnd.current?.scrollIntoView({
      behavior: controller.pending || submission !== null || reduceMotion ? "auto" : "smooth",
      block: "end",
    });
  }, [controller.error, controller.pending, latestMessageText, messageCount, submission, turn?.turnVersion]);
  const pendingQuestion = turn?.status === "completed"
    ? turn.pendingConsultationQuestion
    : turn?.pendingConsultationQuestion ?? pendingConsultationQuestion ?? null;

  if (!turn) {
    return (
      <section className="conversational-rectification" aria-busy={controller.pending} aria-label="生时校正对话">
        {openingAssistantText
          ? <ChatMessageRow message={{
              role: "assistant",
              text: openingAssistantText,
              renderKey: "rectification-opening-assistant",
              state: "streaming",
            }} />
          : <div className="conversational-loading" aria-live="polite" role="status">
              <AppLoadingIndicator title="正在建立校正记录…" detail="正在加载校正进度，准备第一条问题。" />
            </div>}
        {controller.error && <p className="form-error" role="alert">{controller.error}</p>}
      </section>
    );
  }

  const canAnswer = turn.actions.includes("answer") && turn.status !== "abandoned" && turn.status !== "completed";
  const canConfirm = turn.actions.includes("confirm")
    && turn.candidate.status === "ready_for_confirmation"
    && Boolean(turn.candidate.representativeTime);
  const canContinue = turn.actions.includes("continue_original_question")
    && Boolean(pendingQuestion)
    && Boolean(onContinueOriginalQuestion);
  const busy = controller.pending || submission !== null;
  const submit = () => {
    const text = controller.draft.trim();
    if (!canAnswer || !text || busy) return;
    controller.setDraft("");
    setSubmission({ text, phase: "undo", turnVersion: turn.turnVersion });
    undoTimer.current = setTimeout(async () => {
      undoTimer.current = null;
      setSubmission({ text, phase: "generating", turnVersion: turn.turnVersion });
      try {
        await controller.answer(undefined, text);
      } catch {
        controller.setDraft(text);
      } finally {
        setSubmission(null);
        composer.current?.focus();
      }
    }, ANSWER_UNDO_WINDOW_MS);
  };
  const copyMessage = async (message: ConversationalRectificationMessage) => {
    try {
      await navigator.clipboard.writeText(message.text);
      setCopiedMessageKey(message.renderKey);
      window.setTimeout(() => setCopiedMessageKey((current) => (
        current === message.renderKey ? null : current
      )), 1_500);
    } catch {
      // Clipboard permission failures must not interrupt the conversation.
    }
  };
  const regenerateMessage = async (messageKey: string) => {
    setRegeneratingMessageKey(messageKey);
    try {
      await controller.regenerate();
    } finally {
      setRegeneratingMessageKey((current) => current === messageKey ? null : current);
    }
  };
  const undoSubmission = () => {
    if (submission?.phase !== "undo") return;
    if (undoTimer.current) clearTimeout(undoTimer.current);
    undoTimer.current = null;
    controller.setDraft(submission.text);
    setSubmission(null);
    requestAnimationFrame(() => composer.current?.focus());
  };

  return (
    <section className="rectification-chat" aria-busy={busy} aria-label="生时校正对话">
      <div className="message-list rectification-message-list">
        <span className="sr-only" aria-live="polite">{submission?.phase === "undo" ? "消息已发送，可以撤回修改" : controller.pending ? "Jyotisha 正在核对经历" : ""}</span>
        {(controller.messages ?? [{
          role: "assistant" as const,
          text: turn.narrative,
          renderKey: `assistant-${turn.turnVersion}`,
        }]).map((message) => (
          <div className="rectification-message-entry" key={message.renderKey}>
            <ChatMessageRow
              message={regeneratingMessageKey === message.renderKey
                ? { role: "assistant", text: "", renderKey: message.renderKey, state: "thinking" }
                : {
                    role: message.role,
                    text: message.text,
                    renderKey: message.renderKey,
                    state: "settled",
                  }}
            />
            {message.role === "assistant" && regeneratingMessageKey !== message.renderKey && (
              <div className="rectification-message-actions" aria-label="Agent 回答操作">
                <button
                  aria-label="赞"
                  aria-pressed={feedback[message.renderKey] === "up"}
                  className={feedback[message.renderKey] === "up" ? "is-active" : ""}
                  title="赞"
                  type="button"
                  onClick={() => setFeedback((current) => ({
                    ...current,
                    [message.renderKey]: current[message.renderKey] === "up" ? undefined : "up",
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
                    [message.renderKey]: current[message.renderKey] === "down" ? undefined : "down",
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
                  aria-label="重跑回答"
                  disabled={busy || message.renderKey !== latestAssistantKey || !canAnswer}
                  title={message.renderKey === latestAssistantKey ? "重跑" : "只能重跑最新回答"}
                  type="button"
                  onClick={() => safely(regenerateMessage(message.renderKey))}
                >
                  <RotateCcw aria-hidden="true" />
                </button>
              </div>
            )}
          </div>
        ))}
        {submission && turn.turnVersion === submission.turnVersion && (
          <ChatMessageRow
            message={{ role: "user", text: submission.text, renderKey: "pending-evidence", state: "settled" }}
          />
        )}
        {controller.pending && canAnswer && regeneratingMessageKey === null && (
          <ChatMessageRow message={{ role: "assistant", text: "", renderKey: "rectification-thinking", state: "thinking" }} />
        )}
        {controller.error && <p className="error-message" role="alert">{controller.error}</p>}
        <div ref={conversationEnd} />
      </div>

      {(canAnswer || canConfirm || canContinue) && <div className="composer-wrap rectification-composer-wrap">
        {(canConfirm || canContinue) && (
          <div className="composer-suggestions" aria-label="生时校正操作">
            {canConfirm && (
              <button
                aria-label={`确认将 ${turn.candidate.representativeTime} 设为当前排盘时间；当前分钟尚未验证`}
                disabled={busy}
                type="button"
                onClick={() => safely(controller.confirm(turn.candidate.representativeTime ?? undefined))}
              >
                确认采用 {turn.candidate.representativeTime}（尚未验证）
              </button>
            )}
            {canContinue && (
              <button
                disabled={busy || continuationPending}
                type="button"
                onClick={() => onContinueOriginalQuestion?.(pendingQuestion!)}
              >
                {continuationPending ? "正在继续回答…" : "返回原问题"}
              </button>
            )}
          </div>
        )}
        {canAnswer && <>
          {controller.correctionTarget && (
            <div className="rectification-correction-target" role="status">
              <p>正在更正：{controller.correctionTarget.dateLabel} · {controller.correctionTarget.summary}</p>
              <button disabled={busy} type="button" onClick={() => controller.cancelEvidenceCorrection()}>
                取消更正
              </button>
            </div>
          )}
          <form className="composer" onSubmit={(event) => { event.preventDefault(); submit(); }}>
          <label className="sr-only" htmlFor="conversational-rectification-answer">
            {controller.correctionTarget ? "输入更正后的经历" : "回答生时校正问题"}
          </label>
          <Textarea
            id="conversational-rectification-answer"
            ref={composer}
            autoFocus
            disabled={busy}
            maxLength={4_000}
            placeholder={controller.correctionTarget
              ? "例如：更正为 2020 年 11 月离职"
              : "像聊天一样回答即可，例如：2018 年 6 月去了上海工作"}
            rows={2}
            value={controller.draft}
            onChange={(event) => controller.setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
          />
          {submission?.phase === "undo" ? (
            <Button aria-label="撤回发送，本次不计入校正" title="撤回发送" size="icon" type="button" onClick={undoSubmission}>
              <Square aria-hidden="true" />
            </Button>
          ) : (
            <Button aria-label={busy ? "正在核对" : "发送"} disabled={busy || !controller.draft.trim()} size="icon" type="submit">
              <ArrowUp aria-hidden="true" />
            </Button>
          )}
          </form>
          <div className="composer-footer">
            <ModelSelector
              models={models}
              selectedModelId={selectedModelId}
              disabled={busy}
              onSelect={onSelectModel}
            />
          </div>
        </>}
      </div>}
    </section>
  );
}

type ConversationalBirthTimeRectificationProps = Readonly<{
  initialTurn?: ConversationalRectificationTurn | null;
  initialMessages?: readonly ConversationalRectificationStoredMessage[];
  openingAssistantText?: string;
  models: readonly PublicLanguageModel[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onTurn?: (
    turn: ConversationalRectificationTurn,
    messages: readonly ConversationalRectificationMessage[],
  ) => void;
  onPendingChange?: (pending: boolean) => void;
  onContinueOriginalQuestion?: (continuation: RectificationV4Continuation) => void;
}>;

export function ConversationalBirthTimeRectification(props: ConversationalBirthTimeRectificationProps) {
  return (
    <RectificationV4Panel
      pendingConsultationQuestion={props.pendingConsultationQuestion}
      continuationPending={props.continuationPending}
      onPendingChange={props.onPendingChange}
      onContinueOriginalQuestion={props.onContinueOriginalQuestion}
    />
  );
}
