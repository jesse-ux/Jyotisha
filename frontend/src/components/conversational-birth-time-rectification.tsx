"use client";

import { ArrowUp } from "lucide-react";
import { useEffect, useRef } from "react";
import { ChatMessageContent } from "./chat-message-content.tsx";
import { AgentAvatar, ChatMessageRow } from "./chat-message-row.tsx";
import { Button } from "./ui/button.tsx";
import { Textarea } from "./ui/textarea.tsx";
import {
  useConversationalRectification,
  type ConversationalRectificationController,
} from "../hooks/use-conversational-rectification.ts";
import type { ConversationalRectificationTurn } from "../lib/conversational-rectification/contracts.ts";

type EvidenceDomain = NonNullable<
  ConversationalRectificationTurn["evidenceRequest"]
>["domains"][number];

const domainLabels = {
  career: "事业与身份",
  education: "学业与学习",
  finance: "收入与资产",
  health_pressure: "健康与重大压力",
  relocation: "搬迁与居住地",
  relationship: "重要关系",
  family: "家庭变化",
  other: "其他关键经历",
} as const satisfies Readonly<Record<EvidenceDomain, string>>;

function nextEvidenceDomains(turn: ConversationalRectificationTurn): EvidenceDomain[] {
  const provided = new Set(turn.evidenceRecap.flatMap((item) => item.domain ? [item.domain] : []));
  return [...(turn.evidenceRequest?.domains ?? [])]
    .sort((left, right) => Number(provided.has(left)) - Number(provided.has(right)))
    .slice(0, 2);
}

function visibleTurnNarrative(turn: ConversationalRectificationTurn): string {
  if (["paused", "abandoned", "completed"].includes(turn.status)) {
    return turn.narrative;
  }

  const suggestedDomains = nextEvidenceDomains(turn).map((domain) => domainLabels[domain]);
  if (turn.evidenceRecap.length === 0) {
    const examples = suggestedDomains.length > 0
      ? suggestedDomains.join("或")
      : "工作、搬迁、关系或学业";
    return `为了帮助校正出生时间，请先说一件${examples}方面已经发生的重要经历。最好带上年月，直接像聊天一样描述即可。`;
  }

  const latestEvidence = turn.evidenceRecap.at(-1)!;
  if (turn.candidate.status === "ready_for_confirmation") {
    return [
      `${latestEvidence.isCorrection ? "已修订" : "已记录"}：${latestEvidence.dateLabel} · ${latestEvidence.summary}。`,
      "目前已经形成一个待确认候选。你可以展开下方详情核对，也可以继续补充一件带年月的真实经历。",
    ].join("\n\n");
  }

  const candidateRange = turn.candidate.rangeStart && turn.candidate.rangeEnd
    ? `${turn.candidate.rangeStart}–${turn.candidate.rangeEnd}`
    : turn.candidate.representativeTime ?? "当前候选范围";
  const nextQuestion = suggestedDomains.length > 0
    ? `接下来请说一件${suggestedDomains.join("或")}方面已经发生的事，尽量带上年月。`
    : "接下来请再说一件已经发生的真实经历，尽量带上年月。";
  return [
    `${latestEvidence.isCorrection ? "已修订" : "已记录"}：${latestEvidence.dateLabel} · ${latestEvidence.summary}。`,
    `候选范围现在是 ${candidateRange}。范围暂未变化不代表提交失败，我会结合后续经历继续比较相邻分钟。`,
    nextQuestion,
  ].join("\n\n");
}

type SurfaceProps = Readonly<{
  controller: ConversationalRectificationController;
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onContinueOriginalQuestion?: (question: string) => void;
}>;

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
  const turn = controller.turn;
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
  const submit = async () => {
    if (!canAnswer || !controller.draft.trim() || controller.pending) return;
    try {
      await controller.answer(undefined, controller.draft.trim());
      composer.current?.focus();
    } catch {
      // The controller keeps the draft and owns the visible error.
    }
  };

  return (
    <section className="rectification-chat" aria-busy={controller.pending} aria-label="生时校正对话">
      <div className="message-list rectification-message-list">
        <span className="sr-only" aria-live="polite">{controller.pending ? "Jyotisha 正在核对经历" : ""}</span>
        {turn.evidenceRecap.map((entry) => (
          <ChatMessageRow
            key={entry.id}
            message={{
              role: "user",
              text: `${entry.dateLabel} · ${entry.summary}${entry.isCorrection ? "（已修订）" : ""}`,
              renderKey: entry.id,
              state: "settled",
            }}
          />
        ))}
        {controller.pending && controller.draft.trim() && (
          <ChatMessageRow
            message={{ role: "user", text: controller.draft.trim(), renderKey: "pending-evidence", state: "settled" }}
          />
        )}
        <article className="message message-assistant" aria-label="Jyotisha">
          <AgentAvatar />
          <div className="message-content">
            <div className="message-bubble">
              <ChatMessageContent text={visibleTurnNarrative(turn)} />
              <details className="rectification-message-details">
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
                            disabled={controller.pending}
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
            </div>
          </div>
        </article>
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
                disabled={controller.pending}
                type="button"
                onClick={() => safely(controller.confirm(turn.candidate.representativeTime ?? undefined))}
              >
                确认采用 {turn.candidate.representativeTime}（尚未验证）
              </button>
            )}
            {canContinue && (
              <button
                disabled={controller.pending || continuationPending}
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
              <button disabled={controller.pending} type="button" onClick={() => controller.cancelEvidenceCorrection()}>
                取消更正
              </button>
            </div>
          )}
          <form className="composer" onSubmit={(event) => { event.preventDefault(); void submit(); }}>
          <label className="sr-only" htmlFor="conversational-rectification-answer">
            {controller.correctionTarget ? "输入更正后的经历" : "回答生时校正问题"}
          </label>
          <Textarea
            id="conversational-rectification-answer"
            ref={composer}
            autoFocus
            disabled={controller.pending}
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
          <Button aria-label={controller.pending ? "正在核对" : "发送"} disabled={controller.pending || !controller.draft.trim()} size="icon" type="submit">
            <ArrowUp aria-hidden="true" />
          </Button>
          </form>
          <div className="composer-footer">
            <p>{controller.pending ? "正在核对这段经历…" : "Enter 发送 · Shift + Enter 换行"}</p>
          </div>
        </>}
      </div>}
    </section>
  );
}

type ConversationalBirthTimeRectificationProps = Readonly<{
  initialTurn?: ConversationalRectificationTurn | null;
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onTurn?: (turn: ConversationalRectificationTurn) => void;
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
