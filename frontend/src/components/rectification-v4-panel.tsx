"use client";

import { ArrowUp, Check, Pause, Play, Square } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { useRectificationV4 } from "@/hooks/use-rectification-v4";
import type { CandidateCluster, LifeEventRevision } from "@/lib/rectification-v4/contracts";
import { AppLoadingIndicator } from "./app-loading-indicator";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";

const phaseCopy = {
  extracting_evidence: "正在整理经历",
  scoring_candidates: "正在比较候选时间",
  checking_robustness: "正在做稳定性复核",
  planning_question: "正在准备下一步问题",
  collecting_evidence: "正在准备下一步问题",
  complete: "正在整理结果",
} as const;

function minutes(time: string) {
  const [hour = 0, minute = 0] = time.split(":").map(Number);
  return hour * 60 + minute;
}

function inCluster(time: string, cluster: CandidateCluster) {
  const value = minutes(time);
  const start = minutes(cluster.startTime);
  const end = minutes(cluster.endTime);
  return end >= start ? value >= start && value <= end : value >= start || value <= end;
}

function latestEvents(events: readonly LifeEventRevision[]) {
  const latest = new Map<string, LifeEventRevision>();
  for (const event of events) {
    const current = latest.get(event.eventId);
    if (!current || current.revision < event.revision) latest.set(event.eventId, event);
  }
  return [...latest.values()].sort((left, right) => left.dateRange.start.localeCompare(right.dateRange.start));
}

function eventText(event: LifeEventRevision) {
  return `${event.dateRange.label} · ${event.summary}`;
}

export type RectificationV4Continuation = Readonly<{
  protocol: "rectification-evidence-v4";
  question: string;
  caseId: string;
  caseVersion: number;
  acceptedRange: Readonly<{ start: string; end: string }>;
}>;

export function RectificationV4Panel(props: Readonly<{
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onPendingChange?: (pending: boolean) => void;
  onContinueOriginalQuestion?: (continuation: RectificationV4Continuation) => void;
}>) {
  const controller = useRectificationV4({
    pendingConsultationQuestion: props.pendingConsultationQuestion,
    onPendingChange: props.onPendingChange,
  });
  const [draft, setDraft] = useState("");
  const composer = useRef<HTMLTextAreaElement>(null);
  const data = controller.data;
  const caseValue = data?.case;
  const snapshot = caseValue?.latestSnapshot;
  const primary = snapshot?.clusters[0];
  const allEvents = useMemo(() => latestEvents(data?.events ?? []), [data?.events]);
  const eventById = useMemo(() => new Map(allEvents.map((event) => [event.eventId, event])), [allEvents]);
  const evidence = useMemo(() => {
    if (!snapshot || !primary) return { supporting: [] as LifeEventRevision[], conflicting: [] as LifeEventRevision[] };
    const candidates = snapshot.candidates.filter((candidate) => inCluster(candidate.time, primary));
    const supporting = new Set(candidates.flatMap((candidate) => candidate.supportingEventIds));
    const conflicting = new Set(candidates.flatMap((candidate) => candidate.conflictingEventIds));
    return {
      supporting: [...supporting].map((id) => eventById.get(id)).filter((event): event is LifeEventRevision => Boolean(event)),
      conflicting: [...conflicting].map((id) => eventById.get(id)).filter((event): event is LifeEventRevision => Boolean(event)),
    };
  }, [eventById, primary, snapshot]);

  if (controller.loading) {
    return <section className="rectification-v4-panel"><AppLoadingIndicator title="正在打开生时校正" detail="正在恢复已经保存的进度" /></section>;
  }
  if (!caseValue) {
    return <section className="rectification-v4-panel" role="alert"><p>{controller.error || "暂时无法打开生时校正。"}</p></section>;
  }

  const processing = caseValue.status === "processing" || ["pending", "processing"].includes(controller.job?.status ?? "");
  const phase = controller.job?.phase ?? caseValue.phase;
  const canAnswer = Boolean(caseValue.currentQuestion) && !processing && ["awaiting_answer", "range_ready"].includes(caseValue.status);
  const accepted = caseValue.acceptedRange;
  const handoff = controller.handoff;
  const canContinue = Boolean(accepted && handoff?.status === "pending" && props.onContinueOriginalQuestion);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const answer = draft.trim();
    if (!answer || !canAnswer) return;
    const result = await controller.answer(answer);
    if (result) setDraft("");
  }

  return (
    <section className="rectification-v4-panel" aria-busy={processing || controller.pending}>
      <header className="rectification-v4-header">
        <div>
          <p className="rectification-v4-eyebrow">生时校正 · 事件证据法</p>
          <h2>先核对经历，再比较候选时间</h2>
          <p>当前只在 {caseValue.calculationSpec.candidateRange.start}–{caseValue.calculationSpec.candidateRange.end} 内比较。这里显示的是候选范围，不是已确认的出生分钟。</p>
        </div>
        {caseValue.status === "paused" ? (
          <Button type="button" variant="outline" disabled={controller.pending} onClick={() => void controller.resume()}><Play aria-hidden="true" />继续</Button>
        ) : caseValue.status !== "abandoned" && !accepted ? (
          <Button type="button" variant="outline" disabled={processing || controller.pending} onClick={() => void controller.pause()}><Pause aria-hidden="true" />暂停</Button>
        ) : null}
      </header>

      {props.pendingConsultationQuestion && (
        <aside className="rectification-v4-context">
          <b>原问题已保留</b>
          <p>{props.pendingConsultationQuestion}</p>
        </aside>
      )}

      {processing && (
        <div className="rectification-v4-processing" role="status">
          <AppLoadingIndicator title={phaseCopy[phase]} detail="回答已经保存，计算在后台继续" />
          <p>回答已经保存。你可以离开此页，稍后回来继续。</p>
        </div>
      )}

      {snapshot && primary && !processing && (
        <article className="rectification-v4-result">
          <p className="rectification-v4-eyebrow">当前结果</p>
          <div className="rectification-v4-ranges">
            <div><span>主要候选范围</span><strong>{primary.startTime}–{primary.endTime}</strong></div>
            {snapshot.clusters[1] && <div><span>次级候选范围</span><strong>{snapshot.clusters[1].startTime}–{snapshot.clusters[1].endTime}</strong></div>}
          </div>
          <div className="rectification-v4-evidence-grid">
            <div>
              <h3>支持这个范围的经历</h3>
              {evidence.supporting.length > 0 ? <ul>{evidence.supporting.map((event) => <li key={event.id}>{eventText(event)}</li>)}</ul> : <p>现有经历提供了初步支持，但还需要更多不同领域的事件。</p>}
            </div>
            <div>
              <h3>仍有冲突或区分力不足</h3>
              {evidence.conflicting.length > 0 ? <ul>{evidence.conflicting.map((event) => <li key={event.id}>{eventText(event)}</li>)}</ul> : <p>暂未发现明确冲突；范围仍会随新增事件变化。</p>}
            </div>
          </div>
          <p className="rectification-v4-uncertainty">系统只保存通过邻近分钟、逐项排除和日期敏感性复核的范围；不会把峰值分钟当作真实出生时间。</p>
          <div className="rectification-v4-actions">
            {caseValue.currentQuestion && !accepted && <Button type="button" variant="outline" onClick={() => composer.current?.focus()}>继续补充</Button>}
            {snapshot.canAcceptRange && !accepted && <Button type="button" disabled={controller.pending} onClick={() => void controller.acceptRange()}><Check aria-hidden="true" />保存这个范围</Button>}
            {accepted && <span className="rectification-v4-saved"><Check aria-hidden="true" />已保存 {accepted.start}–{accepted.end}</span>}
          </div>
        </article>
      )}

      {caseValue.status === "paused" && <p className="rectification-v4-notice">进度已保存。继续后会从下一道问题开始。</p>}
      {caseValue.status === "abandoned" && <p className="rectification-v4-notice">本次校正已结束，现有出生时间没有被改写。</p>}
      {controller.error && <p className="error-message" role="alert">{controller.error}</p>}

      {canAnswer && (
        <form className="rectification-v4-composer" onSubmit={submit}>
          <label htmlFor="rectification-v4-answer">{caseValue.currentQuestion?.prompt}</label>
          <Textarea
            id="rectification-v4-answer"
            ref={composer}
            value={draft}
            disabled={controller.pending}
            placeholder="例如：2015 年高中毕业后复读一年，2016 年再次毕业。"
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
          />
          <Button aria-label="提交这段经历" disabled={!draft.trim() || controller.pending} size="icon" type="submit"><ArrowUp aria-hidden="true" /></Button>
        </form>
      )}

      <footer className="rectification-v4-footer">
        {canContinue && accepted && handoff && (
          <Button type="button" disabled={props.continuationPending} onClick={() => props.onContinueOriginalQuestion?.({
            protocol: "rectification-evidence-v4",
            question: handoff.question,
            caseId: caseValue.id,
            caseVersion: caseValue.version,
            acceptedRange: accepted,
          })}>
            {props.continuationPending ? "正在回到原问题…" : "带着候选范围继续原问题"}
          </Button>
        )}
        {accepted && handoff?.status === "in_progress" && <span className="rectification-v4-saved">原问题正在另一设备继续回答</span>}
        {accepted && handoff?.status === "consumed" && <span className="rectification-v4-saved"><Check aria-hidden="true" />原问题已继续回答</span>}
        {!accepted && caseValue.status !== "abandoned" && (
          <button type="button" disabled={processing || controller.pending} onClick={() => void controller.abandon()}><Square aria-hidden="true" />结束本次校正</button>
        )}
      </footer>
    </section>
  );
}
