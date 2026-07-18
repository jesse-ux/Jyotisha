"use client";

import { useState } from "react";
import { lifeEventSchema } from "@/lib/birth-time-evidence";
import type { EvidenceDraft } from "@/lib/birth-time-journey-turn";
import type { EvidenceDatePrecision, EvidenceDomain } from "@/lib/birth-time-question-planner";

const domainLabels = {
  education: "学业与学习环境",
  relocation: "搬迁与长期居住地",
  relationship: "重要关系",
  career: "工作与身份变化",
  health_pressure: "健康或生活压力",
} as const satisfies Readonly<Record<EvidenceDomain, string>>;

type DraftCardProps = {
  readonly draft: EvidenceDraft;
  readonly pending: boolean;
  readonly onConfirm: (precision: EvidenceDatePrecision, date: string) => void;
  readonly onSkip: () => void;
};

function parsePrecision(value: string): EvidenceDatePrecision {
  if (value === "year" || value === "month" || value === "day") return value;
  throw new TypeError("Unsupported evidence date precision");
}

export function BirthTimeEvidenceDraftCard(props: DraftCardProps) {
  const [precision, setPrecision] = useState<EvidenceDatePrecision>(props.draft.precision ?? "year");
  const [date, setDate] = useState(props.draft.date ?? "");
  const isValid = lifeEventSchema.safeParse({
    id: props.draft.draftId,
    domain: props.draft.domain,
    precision,
    date,
  }).success;
  const inputType = precision === "year" ? "number" : precision;

  return (
    <div className="birth-time-evidence-draft-card">
      <div className="birth-time-candidate-heading"><b>确认关键经历</b><span>待确认草稿</span></div>
      <dl className="birth-time-draft-domain"><div><dt>经历领域</dt><dd>{domainLabels[props.draft.domain]}</dd></div></dl>
      <div className="birth-time-draft-fields">
        <label>
          <span>记得的精度</span>
          <select disabled={props.pending} value={precision} onChange={(event) => { setPrecision(parsePrecision(event.target.value)); setDate(""); }}>
            <option value="year">只记得年份</option>
            <option value="month">记得月份</option>
            <option value="day">记得具体日期</option>
          </select>
        </label>
        <label>
          <span>发生时间</span>
          <input
            aria-invalid={date.length > 0 && !isValid}
            disabled={props.pending}
            inputMode={precision === "year" ? "numeric" : undefined}
            max={precision === "year" ? String(new Date().getFullYear()) : undefined}
            min={precision === "year" ? "1900" : undefined}
            type={inputType}
            value={date}
            onChange={(event) => setDate(event.target.value)}
          />
        </label>
      </div>
      {!isValid && <p className="form-error" role="alert">请填写与所选精度一致的有效日期；<span className="phrase-nowrap">不会自动补猜缺失时间</span>。</p>}
      <div className="birth-time-guided-actions">
        <button className="button-secondary birth-time-guided-action" disabled={props.pending} type="button" onClick={props.onSkip}>放弃这条并跳过</button>
        <button className="button-primary birth-time-guided-action" disabled={props.pending || !isValid} type="button" onClick={() => props.onConfirm(precision, date)}>
          {props.pending ? "确认中…" : "确认并用于校正"}
        </button>
      </div>
    </div>
  );
}
