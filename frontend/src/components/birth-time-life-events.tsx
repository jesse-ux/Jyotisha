"use client";

import { useRef, useState } from "react";
import { lifeEventSchema } from "@/lib/birth-time-journey";
import type { LifeEvent } from "@/lib/birth-time-evidence";

type EventDraft = {
  readonly rowId: string;
  readonly eventId: string;
  readonly domain: LifeEvent["domain"] | "";
  readonly precision: LifeEvent["precision"];
  readonly date: string;
};

type BirthTimeLifeEventsProps = {
  readonly initialEvents: readonly LifeEvent[];
  readonly pending: boolean;
  readonly onSubmit: (events: readonly LifeEvent[]) => void;
};

const domainOptions = [
  { value: "education", label: "学业或学习方向" },
  { value: "relocation", label: "搬家、离乡或长期异地" },
  { value: "relationship", label: "重要关系节点" },
  { value: "career", label: "工作或身份变化" },
  { value: "health_pressure", label: "健康、事故或低谷" },
] as const;

const initialDomains = ["education", "career", "relationship"] as const;

function initialDrafts(events: readonly LifeEvent[]): readonly EventDraft[] {
  if (events.length > 0) {
    return events.map((event, index) => ({
      rowId: `stored-${index}`,
      eventId: event.id,
      domain: event.domain,
      precision: event.precision,
      date: event.date,
    }));
  }
  return initialDomains.map((domain, index) => ({
    rowId: `initial-${index}`,
    eventId: "",
    domain,
    precision: "month",
    date: "",
  }));
}

function dateInputType(precision: LifeEvent["precision"]) {
  switch (precision) {
    case "year": return "number";
    case "month": return "month";
    case "day": return "date";
  }
}

function parseDomain(value: string): EventDraft["domain"] {
  switch (value) {
    case "":
    case "education":
    case "relocation":
    case "relationship":
    case "career":
    case "health_pressure":
      return value;
    default:
      return "";
  }
}

function parsePrecision(value: string): EventDraft["precision"] {
  switch (value) {
    case "year":
    case "month":
    case "day":
      return value;
    default:
      return "month";
  }
}

export function BirthTimeLifeEvents({
  initialEvents,
  pending,
  onSubmit,
}: BirthTimeLifeEventsProps) {
  const [drafts, setDrafts] = useState(() => initialDrafts(initialEvents));
  const [error, setError] = useState("");
  const nextRowId = useRef(0);

  function patchDraft(rowId: string, patch: Partial<EventDraft>) {
    setDrafts((current) => current.map((draft) => (
      draft.rowId === rowId ? { ...draft, ...patch } : draft
    )));
  }

  function addDraft() {
    setDrafts((current) => current.length >= 6 ? current : [...current, {
      rowId: `added-${nextRowId.current++}`,
      eventId: "",
      domain: "",
      precision: "month",
      date: "",
    }]);
  }

  function removeDraft(rowId: string) {
    setDrafts((current) => current.length <= 3
      ? current
      : current.filter((draft) => draft.rowId !== rowId));
  }

  function submit() {
    const parsed = drafts.map((draft) => lifeEventSchema.safeParse({
      id: draft.eventId || crypto.randomUUID(),
      domain: draft.domain,
      precision: draft.precision,
      date: draft.date,
    }));
    if (parsed.some((item) => !item.success)) {
      setError("请为每条经历选择类型，并填写与精度一致的日期。");
      return;
    }
    const events = parsed.flatMap((item) => item.success ? [item.data] : []);
    if (new Set(events.map((event) => event.domain)).size < 2) {
      setError("请至少选择两个不同领域的经历，以便区分候选时间。");
      return;
    }
    setError("");
    onSubmit(events);
  }

  return (
    <div className="birth-time-life-events">
      <div className="birth-time-question-progress">
        <b>关键经历日期</b>
        <span>{drafts.length} / 6</span>
      </div>
      <p className="birth-time-evidence-note">
        请填写至少三条、覆盖两个领域的经历。只使用日期和类型评分，不会从描述中猜测。
      </p>
      <div className="birth-time-event-list">
        {drafts.map((draft, index) => (
          <fieldset className="birth-time-event-row" key={draft.rowId}>
            <legend>经历 {index + 1}</legend>
            <label>
              <span>经历类型</span>
              <select
                required
                value={draft.domain}
                onChange={(event) => patchDraft(draft.rowId, { domain: parseDomain(event.target.value) })}
              >
                <option value="">请选择</option>
                {domainOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <label>
              <span>记得的精度</span>
              <select
                value={draft.precision}
                onChange={(event) => patchDraft(draft.rowId, {
                  precision: parsePrecision(event.target.value),
                  date: "",
                })}
              >
                <option value="year">只记得年份</option>
                <option value="month">记得月份</option>
                <option value="day">记得具体日期</option>
              </select>
            </label>
            <label>
              <span>发生时间</span>
              <input
                required
                inputMode={draft.precision === "year" ? "numeric" : undefined}
                min={draft.precision === "year" ? "1900" : undefined}
                max={draft.precision === "year" ? String(new Date().getFullYear()) : undefined}
                type={dateInputType(draft.precision)}
                value={draft.date}
                onChange={(event) => patchDraft(draft.rowId, { date: event.target.value })}
              />
            </label>
            {drafts.length > 3 && (
              <button className="button-text birth-time-event-remove" type="button" onClick={() => removeDraft(draft.rowId)}>
                移除这条
              </button>
            )}
          </fieldset>
        ))}
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="birth-time-evidence-actions">
        <button className="button-secondary" disabled={pending || drafts.length >= 6} type="button" onClick={addDraft}>
          添加经历
        </button>
        <button className="button-primary" disabled={pending} type="button" onClick={submit}>
          {pending ? "正在比较候选…" : "比较候选时间"}
        </button>
      </div>
    </div>
  );
}
