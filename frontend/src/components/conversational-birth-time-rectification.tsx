"use client";

import { ArrowUp, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { ChatMessageRow } from "./chat-message-row.tsx";
import { Button } from "./ui/button.tsx";
import { Textarea } from "./ui/textarea.tsx";
import {
  useConversationalRectification,
  type ConversationalRectificationController,
} from "../hooks/use-conversational-rectification.ts";
import type {
  ConversationalRectificationResponse,
  ConversationalRectificationTurn,
} from "../lib/conversational-rectification/contracts.ts";

type SurfaceProps = Readonly<{
  controller: ConversationalRectificationController;
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onContinueOriginalQuestion?: (question: string) => void;
}>;

const ANSWER_UNDO_WINDOW_MS = 2_500;

function safely(request: Promise<unknown>) {
  void request.catch(() => undefined);
}

function candidateStatus(turn: ConversationalRectificationTurn): string {
  if (turn.status === "completed" && turn.candidate.status === "confirmed") return "已确认";
  if (turn.status === "completed") return "范围已保存，分钟未确认";
  if (turn.candidate.status === "ready_for_confirmation") return "待确认，尚未验证";
  return "待验证";
}

export function ConversationalRectificationSurface({
  controller,
  pendingConsultationQuestion,
  continuationPending = false,
  onContinueOriginalQuestion,
}: SurfaceProps) {
  const composer = useRef<HTMLTextAreaElement>(null);
  const undoTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [submission, setSubmission] = useState<Readonly<{
    text: string;
    phase: "undo" | "generating";
    turnVersion: number;
  }> | null>(null);
  const turn = controller.turn;
  useEffect(() => () => {
    if (undoTimer.current) clearTimeout(undoTimer.current);
  }, []);
  const pendingQuestion = turn?.status === "completed"
    ? turn.pendingConsultationQuestion
    : turn?.pendingConsultationQuestion ?? pendingConsultationQuestion ?? null;

  if (!turn) {
    return (
      <section className="conversational-rectification" aria-busy={controller.pending} aria-label="生时校正对话">
        <p className="conversational-empty-state" aria-live="polite" role="status">正在建立校正记录…</p>
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
          <ChatMessageRow
            key={message.renderKey}
            message={{
              role: message.role,
              text: message.text,
              renderKey: message.renderKey,
              state: "settled",
            }}
          />
        ))}
        {submission && turn.turnVersion === submission.turnVersion && (
          <ChatMessageRow
            message={{ role: "user", text: submission.text, renderKey: "pending-evidence", state: "settled" }}
          />
        )}
        <details className="rectification-message-details rectification-progress-details">
                <summary>
                  {turn.candidate.representativeTime
                    ? `当前候选 ${turn.candidate.representativeTime} · ${candidateStatus(turn)}`
                    : `校正进度 · ${candidateStatus(turn)}`}
                </summary>
                <p>
                  {turn.candidate.rangeStart && turn.candidate.rangeEnd
                    ? `候选范围 ${turn.candidate.rangeStart}—${turn.candidate.rangeEnd}；已记录 ${turn.evidenceRecap.length} 条经历。`
                    : `已记录 ${turn.evidenceRecap.length} 条经历，尚未缩小候选范围。`}
                </p>
                <p>候选只用于继续验证；这一步不会自动采用候选，未经发布门禁与明确确认不会成为当前排盘时间。</p>
                {turn.evidenceRecap.length > 0 && (
                  <ul aria-label="已记录的真实经历">
                    {turn.evidenceRecap.map((entry) => (
                      <li key={entry.id}>
                        <span>{entry.dateLabel} · {entry.summary}{entry.isCorrection ? "（已修订）" : ""}</span>
                        {canAnswer && (
                          <button
                            aria-label={`更正这条经历：${entry.summary}`}
                            disabled={busy}
                            type="button"
                            onClick={() => {
                              controller.beginEvidenceCorrection(entry.id);
                              composer.current?.focus();
                            }}
                          >
                            更正
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
        </details>
        {controller.pending && canAnswer && (
          <ChatMessageRow message={{ role: "assistant", text: "", renderKey: "rectification-thinking", state: "thinking" }} />
        )}
        {turn.status === "paused" && <ChatMessageRow message={{ role: "assistant", text: "校正已暂停，输入与现有证据都已保留。", renderKey: "rectification-paused", state: "settled" }} />}
        {turn.status === "abandoned" && <ChatMessageRow message={{ role: "assistant", text: "本次校正已放弃，候选时间没有应用。", renderKey: "rectification-abandoned", state: "settled" }} />}
        {turn.status === "completed" && <ChatMessageRow message={{
          role: "assistant",
          text: turn.candidate.status === "confirmed"
            ? "候选时间已经过你的明确确认。"
            : "候选范围已保存，代表时间没有自动设为当前排盘时间。",
          renderKey: "rectification-completed",
          state: "settled",
        }} />}
        {controller.error && <p className="error-message" role="alert">{controller.error}</p>}
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
            <p>{submission?.phase === "undo"
              ? "已发送，2.5 秒内可撤回修改，本次不会计入校正。"
              : busy ? "正在核对这段经历…" : "Enter 发送 · Shift + Enter 换行"}</p>
          </div>
        </>}
      </div>}
    </section>
  );
}

type ConversationalBirthTimeRectificationProps = Readonly<{
  initialTurn?: ConversationalRectificationResponse | null;
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onTurn?: (turn: ConversationalRectificationResponse) => void;
  onPendingChange?: (pending: boolean) => void;
  onContinueOriginalQuestion?: (question: string) => void;
}>;

export function ConversationalBirthTimeRectification(props: ConversationalBirthTimeRectificationProps) {
  const pendingChange = useRef(props.onPendingChange);
  useEffect(() => {
    pendingChange.current = props.onPendingChange;
  }, [props.onPendingChange]);
  useEffect(() => () => pendingChange.current?.(false), []);
  const controller = useConversationalRectification({
    initialTurn: props.initialTurn,
    onTurn: props.onTurn,
    onPendingChange: props.onPendingChange,
  });
  return (
    <ConversationalRectificationSurface
      controller={controller}
      pendingConsultationQuestion={props.pendingConsultationQuestion}
      continuationPending={props.continuationPending}
      onContinueOriginalQuestion={props.onContinueOriginalQuestion}
    />
  );
}
