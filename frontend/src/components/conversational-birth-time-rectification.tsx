"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";
import { ChatMessageContent } from "./chat-message-content.tsx";
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
  relocation: "搬迁与居住地",
  relationship: "重要关系",
  family: "家庭变化",
  other: "其他关键经历",
} as const satisfies Readonly<Record<EvidenceDomain, string>>;

type SurfaceProps = Readonly<{
  controller: ConversationalRectificationController;
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onContinueOriginalQuestion?: (question: string) => void;
}>;

function safely(request: Promise<unknown>) {
  void request.catch(() => undefined);
}

function CandidateSummary({ turn }: { readonly turn: ConversationalRectificationTurn }) {
  const candidate = turn.candidate;
  const confirmed = candidate.status === "confirmed" && turn.status === "completed";
  const status = confirmed
    ? "已明确确认"
    : turn.status === "completed"
      ? "范围已保存 · 分钟未确认"
    : candidate.status === "ready_for_confirmation"
      ? "待确认 · 未验证"
      : "待验证 · 未确认";

  return (
    <section className="conversational-candidate" aria-labelledby="conversational-candidate-title">
      <header>
        <h3 id="conversational-candidate-title">候选时间</h3>
        <span className={confirmed ? "is-confirmed" : "is-unverified"}>{status}</span>
      </header>
      {candidate.representativeTime ? (
        <dl>
          <div>
            <dt>代表时间</dt>
            <dd><time dateTime={candidate.representativeTime}>{candidate.representativeTime}</time></dd>
          </div>
          <div>
            <dt>候选范围</dt>
            <dd>{candidate.rangeStart && candidate.rangeEnd
              ? `${candidate.rangeStart}—${candidate.rangeEnd}`
              : "尚未缩小"}</dd>
          </div>
        </dl>
      ) : <p>尚未形成可供确认的具体时间。</p>}
      {!confirmed && <p>候选仍待真实经历验证，未经你的明确确认不会成为当前排盘时间。</p>}
    </section>
  );
}

export function ConversationalRectificationSurface({
  controller,
  pendingConsultationQuestion,
  continuationPending = false,
  onContinueOriginalQuestion,
}: SurfaceProps) {
  const composer = useRef<HTMLTextAreaElement>(null);
  const [eventYear, setEventYear] = useState("");
  const [eventMonth, setEventMonth] = useState("");
  const currentYear = new Date().getFullYear();
  const eventYears = Array.from({ length: 101 }, (_, index) => currentYear - index);
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
  const requestedDomains = turn.evidenceRequest?.domains ?? [];
  const submit = async () => {
    if (!canAnswer || !controller.draft.trim() || controller.pending) return;
    const dateLabel = eventYear
      ? `${eventYear} 年${eventMonth ? ` ${Number(eventMonth)} 月` : ""}`
      : "时间不确定";
    const answer = `发生时间：${dateLabel}\n事件详情：${controller.draft.trim()}`;
    try {
      await controller.answer(undefined, answer);
      setEventYear("");
      setEventMonth("");
    } catch {
      // The controller owns the visible request error and keeps the draft available for retry.
    }
  };
  const focusComposer = () => composer.current?.focus();

  return (
    <section
      className="conversational-rectification"
      aria-busy={controller.pending}
      aria-label="生时校正对话"
    >
      <CandidateSummary turn={turn} />

      <article className="conversational-narrative" aria-label="校正分析">
        <div className="conversational-narrative-body">
          <ChatMessageContent text={turn.narrative} />
        </div>
      </article>

      {requestedDomains.length > 0 && (
        <fieldset className="conversational-domain-picker">
          <legend className="conversational-domain-question">这轮想先补充哪个领域？</legend>
          <div>
            {requestedDomains.map((domain) => (
              <button
                aria-pressed={controller.selectedDomain === domain}
                data-evidence-domain={domain}
                disabled={controller.pending || !canAnswer}
                key={domain}
                type="button"
                onClick={() => {
                  controller.selectDomain(domain);
                  focusComposer();
                }}
              >
                {domainLabels[domain]}
              </button>
            ))}
          </div>
        </fieldset>
      )}

      {canAnswer && <form
        className="conversational-composer"
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        {controller.correctionTarget && (
          <div className="conversational-correction-target" role="status">
            <p>
              正在更正：<strong>{controller.correctionTarget.dateLabel} · {controller.correctionTarget.summary}</strong>
            </p>
            <span>一次只更正一条事件。提交后会保留原记录用于审计，但候选评分只使用更正后的有效证据。</span>
            <button
              className="button-secondary"
              disabled={controller.pending}
              type="button"
              onClick={() => controller.cancelEvidenceCorrection()}
            >
              取消更正
            </button>
          </div>
        )}
        <label htmlFor="conversational-rectification-answer">
          {controller.correctionTarget ? "填写更正后的真实经历" : "补充真实经历"}
          <span>大概年份也可以；不确定的部分请直接说不确定。</span>
        </label>
        <div className="conversational-event-date" role="group" aria-label="经历发生时间">
          <label>
            年份
            <select
              aria-label="经历发生年份"
              disabled={controller.pending || !canAnswer}
              value={eventYear}
              onChange={(event) => {
                setEventYear(event.target.value);
                if (!event.target.value) setEventMonth("");
              }}
            >
              <option value="">不确定</option>
              {eventYears.map((year) => <option key={year} value={year}>{year} 年</option>)}
            </select>
          </label>
          <label>
            月份（可选）
            <select
              aria-label="经历发生月份"
              disabled={controller.pending || !canAnswer || !eventYear}
              value={eventMonth}
              onChange={(event) => setEventMonth(event.target.value)}
            >
              <option value="">不确定</option>
              {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                <option key={month} value={month}>{month} 月</option>
              ))}
            </select>
          </label>
        </div>
        <textarea
          id="conversational-rectification-answer"
          disabled={controller.pending || !canAnswer}
          maxLength={4_000}
          placeholder={controller.correctionTarget
            ? "例如：其实是 2020 年 11 月离职"
            : "请描述一件已经发生的具体事件"}
          ref={composer}
          rows={4}
          value={controller.draft}
          onChange={(event) => controller.setDraft(event.target.value)}
          onKeyDown={(event) => {
            if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
              event.preventDefault();
              void submit();
            }
          }}
        />
        <div className="conversational-composer-footer">
          <small>Ctrl/⌘ + Enter 发送</small>
          <button
            className="button-primary"
            disabled={controller.pending || !canAnswer || !controller.draft.trim()}
            type="submit"
          >
            {controller.pending ? "正在核对…" : "发送这段经历"}
          </button>
        </div>
      </form>}

      {turn.evidenceRecap.length > 0 && (
        <section className="conversational-evidence-recap" aria-labelledby="conversational-evidence-title">
          <header>
            <h3 id="conversational-evidence-title">已记录的真实经历</h3>
            <span>{turn.evidenceRecap.length} 条</span>
          </header>
          <ul>
            {turn.evidenceRecap.map((entry) => (
              <li key={entry.id}>
                <div>
                  <time>{entry.dateLabel}</time>
                  <p>{entry.summary}</p>
                  {entry.isCorrection && <span className="conversational-correction-badge">已修订</span>}
                </div>
                <button
                  aria-label={`更正这条经历：${entry.summary}`}
                  disabled={controller.pending || !canAnswer}
                  type="button"
                  onClick={() => {
                    controller.beginEvidenceCorrection(entry.id);
                    focusComposer();
                  }}
                >
                  更正
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {turn.actions.includes("confirm")
        && turn.candidate.status === "ready_for_confirmation"
        && turn.candidate.representativeTime && (
          <section className="conversational-confirmation" aria-labelledby="conversational-confirmation-title">
            <h3 id="conversational-confirmation-title">采用候选前请明确确认</h3>
            <p>这一步不会自动采用候选。确认后，原始填报时间仍会保留。</p>
            <button
              className="button-primary"
              disabled={controller.pending}
              type="button"
              onClick={() => safely(controller.confirm(turn.candidate.representativeTime ?? undefined))}
            >
              {controller.pending
                ? "确认中…"
                : `确认将 ${turn.candidate.representativeTime} 设为当前排盘时间`}
            </button>
          </section>
        )}

      <div
        aria-live="polite"
        className="conversational-status"
      >
        {turn.status === "paused" && <p>校正已暂停，输入与现有证据都已保留。</p>}
        {turn.status === "abandoned" && <p>本次校正已放弃，候选时间没有应用。</p>}
        {turn.status === "completed" && turn.candidate.status === "confirmed"
          && <p>候选时间已经过你的明确确认。</p>}
        {turn.status === "completed" && turn.candidate.status !== "confirmed"
          && <p>本次校正已结束并保存候选范围；没有把候选代表时间设为当前排盘时间。</p>}
        {controller.error && <p className="form-error" role="alert">{controller.error}</p>}
      </div>

      {turn.actions.includes("continue_original_question")
        && pendingQuestion
        && onContinueOriginalQuestion && (
        <section className="conversational-original-question">
          <p>原问题：{pendingQuestion}</p>
          <button
            className="button-primary"
            disabled={controller.pending || continuationPending}
            type="button"
            onClick={() => onContinueOriginalQuestion?.(pendingQuestion)}
          >
            {continuationPending
              ? "正在继续回答原问题…"
              : turn.candidate.status === "confirmed"
                ? "使用新确认时间继续回答原问题"
                : "返回原对话并继续回答"}
          </button>
        </section>
      )}

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

export function ConversationalBirthTimeRectification(
  props: ConversationalBirthTimeRectificationProps,
) {
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
