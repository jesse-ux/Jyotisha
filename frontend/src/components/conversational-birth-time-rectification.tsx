"use client";

import {
  useEffect,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
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
  relocation: "搬迁与居住地",
  relationship: "重要关系",
  family: "家庭变化",
  other: "其他关键经历",
} as const satisfies Readonly<Record<EvidenceDomain, string>>;

type SurfaceProps = Readonly<{
  controller: ConversationalRectificationController;
  pendingConsultationQuestion?: string | null;
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

function TechnicalReceipt({ turn }: { readonly turn: ConversationalRectificationTurn }) {
  const receipt = turn.technicalReceipt;
  return (
    <details className="conversational-technical-receipt">
      <summary>本轮技术回执</summary>
      <dl>
        <div><dt>计算版本</dt><dd><code>{receipt.calculationVersion}</code></dd></div>
        <div><dt>稳定层</dt><dd>{receipt.stableLayers.join("、") || "无"}</dd></div>
        <div><dt>分钟敏感层</dt><dd>{receipt.sensitiveLayers.join("、") || "无"}</dd></div>
        <div><dt>候选差异引用</dt><dd>{receipt.candidateDifferenceRefs.join("、") || "无"}</dd></div>
      </dl>
    </details>
  );
}

export function ConversationalRectificationSurface({
  controller,
  pendingConsultationQuestion,
  onContinueOriginalQuestion,
}: SurfaceProps) {
  const [abandonArmedFor, setAbandonArmedFor] = useState<string | null>(null);
  const [localAnnouncement, setLocalAnnouncement] = useState<Readonly<{
    identity: string;
    message: string;
  }> | null>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const abandonTrigger = useRef<HTMLButtonElement>(null);
  const abandonCancel = useRef<HTMLButtonElement>(null);
  const abandonConfirm = useRef<HTMLButtonElement>(null);
  const terminalStatus = useRef<HTMLDivElement>(null);
  const restoreAbandonFocus = useRef(false);
  const focusTerminalForCase = useRef<string | null>(null);
  const turn = controller.turn;
  const pendingQuestion = turn?.pendingConsultationQuestion ?? pendingConsultationQuestion ?? null;
  const abandonIdentity = turn
    ? `${turn.caseId}:${turn.turnVersion}:${turn.status}`
    : null;
  const canAbandon = Boolean(
    turn?.actions.includes("abandon")
    && turn.status !== "abandoned"
    && turn.status !== "completed",
  );
  const abandonArmed = canAbandon && abandonArmedFor === abandonIdentity;
  const statusAnnouncement = localAnnouncement?.identity === abandonIdentity
    ? localAnnouncement.message
    : "";

  useEffect(() => {
    if (abandonArmed) {
      abandonCancel.current?.focus();
      return;
    }
    if (restoreAbandonFocus.current) {
      restoreAbandonFocus.current = false;
      abandonTrigger.current?.focus();
    }
  }, [abandonArmed]);

  useEffect(() => {
    const requestedCase = focusTerminalForCase.current;
    if (!requestedCase) return;
    if (!turn || turn.caseId !== requestedCase) {
      focusTerminalForCase.current = null;
      return;
    }
    if (turn.status === "abandoned") {
      focusTerminalForCase.current = null;
      terminalStatus.current?.focus();
    }
  }, [turn]);

  if (!turn) {
    return (
      <section className="conversational-rectification" aria-busy={controller.pending} aria-label="生时校正对话">
        <div className="conversational-empty-state" aria-live="polite">
          <p>系统会先说明候选边界，再邀请你提供已经发生的真实经历。</p>
          <button
            className="button-primary"
            disabled={controller.pending}
            type="button"
            onClick={() => safely(controller.start(pendingQuestion))}
          >
            {controller.pending ? "正在建立校正记录…" : "开始生时校正"}
          </button>
        </div>
        {controller.error && <p className="form-error" role="alert">{controller.error}</p>}
      </section>
    );
  }

  const canAnswer = turn.actions.includes("answer") && turn.status !== "abandoned" && turn.status !== "completed";
  const requestedDomains = turn.evidenceRequest?.domains ?? [];
  const submit = () => {
    if (canAnswer && controller.draft.trim() && !controller.pending) safely(controller.answer());
  };
  const focusComposer = () => composer.current?.focus();
  const continueLocally = () => {
    if (abandonIdentity) {
      setLocalAnnouncement({
        identity: abandonIdentity,
        message: "现在可以继续填写真实经历，输入框已就绪；发送后才会推进校正进度。",
      });
    }
    focusComposer();
  };
  const closeAbandonDialog = () => {
    restoreAbandonFocus.current = true;
    setAbandonArmedFor(null);
  };
  const handleAbandonDialogKey = (event: ReactKeyboardEvent<HTMLElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeAbandonDialog();
      return;
    }
    if (event.key !== "Tab") return;
    if (event.shiftKey && document.activeElement === abandonCancel.current) {
      event.preventDefault();
      abandonConfirm.current?.focus();
    } else if (!event.shiftKey && document.activeElement === abandonConfirm.current) {
      event.preventDefault();
      abandonCancel.current?.focus();
    }
  };
  const confirmAbandon = () => {
    focusTerminalForCase.current = turn.caseId;
    void controller.abandon().catch(() => {
      if (focusTerminalForCase.current === turn.caseId) {
        focusTerminalForCase.current = null;
      }
    });
  };

  return (
    <section
      className="conversational-rectification"
      aria-busy={controller.pending}
      aria-label="生时校正对话"
    >
      <article className="conversational-narrative" aria-label="校正分析">
        <ChatMessageContent text={turn.narrative} />
      </article>

      {requestedDomains.length > 0 && (
        <fieldset className="conversational-domain-picker">
          <legend>这轮想先补充哪个领域？</legend>
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

      <form
        className="conversational-composer"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <label htmlFor="conversational-rectification-answer">
          补充或更正真实经历
          <span>大概年份也可以；不确定的部分请直接说不确定。</span>
        </label>
        <textarea
          id="conversational-rectification-answer"
          disabled={controller.pending || !canAnswer}
          maxLength={4_000}
          ref={composer}
          rows={4}
          value={controller.draft}
          onChange={(event) => controller.setDraft(event.target.value)}
          onKeyDown={(event) => {
            if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
              event.preventDefault();
              submit();
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
      </form>

      {turn.evidenceRecap.length > 0 && (
        <section className="conversational-evidence-recap" aria-labelledby="conversational-evidence-title">
          <header>
            <h3 id="conversational-evidence-title">已记录的真实经历</h3>
            <span>{turn.evidenceRecap.length} 条</span>
          </header>
          <ul>
            {turn.evidenceRecap.map((entry) => (
              <li key={entry.id}>
                <div><time>{entry.dateLabel}</time><p>{entry.summary}</p></div>
                <button
                  aria-label={`更正这条经历：${entry.summary}`}
                  disabled={controller.pending || !canAnswer}
                  type="button"
                  onClick={() => {
                    controller.setDraft(`更正「${entry.summary}」（${entry.dateLabel}）：`);
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

      <CandidateSummary turn={turn} />
      <TechnicalReceipt turn={turn} />

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
        aria-label={turn.status === "abandoned" ? "生时校正终态" : undefined}
        aria-live="polite"
        className="conversational-status"
        ref={terminalStatus}
        tabIndex={turn.status === "abandoned" ? -1 : undefined}
      >
        {turn.status === "paused" && <p>校正已暂停，输入与现有证据都已保留。</p>}
        {turn.status === "abandoned" && <p>本次校正已放弃，候选时间没有应用。</p>}
        {turn.status === "completed" && turn.candidate.status === "confirmed"
          && <p>候选时间已经过你的明确确认。</p>}
        {statusAnnouncement && <p>{statusAnnouncement}</p>}
        {controller.error && <p className="form-error" role="alert">{controller.error}</p>}
      </div>

      {turn.actions.includes("continue_original_question") && pendingQuestion && (
        <section className="conversational-original-question">
          <p>原问题：{pendingQuestion}</p>
          <button
            className="button-primary"
            disabled={controller.pending}
            type="button"
            onClick={() => onContinueOriginalQuestion?.(pendingQuestion)}
          >
            继续回答原问题
          </button>
        </section>
      )}

      <footer className="conversational-session-actions">
        {turn.status === "paused" ? (
          <button
            className="button-secondary"
            disabled={controller.pending}
            type="button"
            onClick={continueLocally}
          >
            继续校正
          </button>
        ) : turn.actions.includes("pause") ? (
          <button
            className="button-secondary"
            disabled={controller.pending}
            type="button"
            onClick={() => safely(controller.pause())}
          >
            暂停，稍后继续
          </button>
        ) : null}

        {canAbandon && !abandonArmed && (
          <button
            className="conversational-abandon"
            disabled={controller.pending}
            ref={abandonTrigger}
            type="button"
            onClick={() => {
              setLocalAnnouncement(null);
              setAbandonArmedFor(abandonIdentity);
            }}
          >
            放弃本次校正
          </button>
        )}
      </footer>

      {abandonArmed && (
        <div className="conversational-abandon-scrim">
          <section
            aria-describedby="conversational-abandon-description"
            aria-labelledby="conversational-abandon-title"
            aria-modal="true"
            className="conversational-abandon-confirmation"
            onKeyDown={handleAbandonDialogKey}
            role="alertdialog"
          >
            <h3 id="conversational-abandon-title">确认放弃本次校正？</h3>
            <p id="conversational-abandon-description">
              放弃后会保留审计记录，但不会应用任何候选时间。
            </p>
            <div>
              <button
                className="button-secondary"
                disabled={controller.pending}
                ref={abandonCancel}
                type="button"
                onClick={closeAbandonDialog}
              >
                返回校正
              </button>
              <button
                className="conversational-abandon is-confirm"
                disabled={controller.pending}
                ref={abandonConfirm}
                type="button"
                onClick={confirmAbandon}
              >
                确认放弃且不应用候选
              </button>
            </div>
          </section>
        </div>
      )}
    </section>
  );
}

type ConversationalBirthTimeRectificationProps = Readonly<{
  initialTurn?: ConversationalRectificationTurn | null;
  pendingConsultationQuestion?: string | null;
  onTurn?: (turn: ConversationalRectificationTurn) => void;
  onContinueOriginalQuestion?: (question: string) => void;
}>;

export function ConversationalBirthTimeRectification(
  props: ConversationalBirthTimeRectificationProps,
) {
  const controller = useConversationalRectification({
    initialTurn: props.initialTurn,
    onTurn: props.onTurn,
  });
  return (
    <ConversationalRectificationSurface
      controller={controller}
      pendingConsultationQuestion={props.pendingConsultationQuestion}
      onContinueOriginalQuestion={props.onContinueOriginalQuestion}
    />
  );
}
