"use client";

import { useId } from "react";
import { BirthDatePicker } from "@/components/birth-date-picker";
import { birthTimeConsultationOptionsCopy } from "@/lib/birth-time-consultation-consent";
import {
  birthTimeDisplayState,
  birthTimePeriodOptions,
  birthTimeSourceOptions,
  type BirthTimeDraft,
  type BirthTimeDraftPatch,
  type BirthTimeSource,
} from "@/lib/birth-time-intake-model";

type BirthTimeIntakeProps = {
  readonly value: BirthTimeDraft;
  readonly onPatch: (patch: BirthTimeDraftPatch) => void;
};

const sourceDefaults = {
  hospital_record: {
    birthTimePeriod: "",
    birthTimeClue: "",
    uncertaintyBeforeMinutes: 2,
    uncertaintyAfterMinutes: 2,
  },
  family_exact: {
    birthTimePeriod: "",
    birthTimeClue: "",
    uncertaintyBeforeMinutes: 10,
    uncertaintyAfterMinutes: 10,
  },
  approximate: {
    birthTimePeriod: "",
    birthTimeClue: "",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
  },
  period_only: {
    reportedTime: "",
    birthTimeClue: "",
    uncertaintyBeforeMinutes: null,
    uncertaintyAfterMinutes: null,
  },
  unknown: {
    reportedTime: "",
    birthTimePeriod: "",
    uncertaintyBeforeMinutes: null,
    uncertaintyAfterMinutes: null,
  },
} as const satisfies Record<Exclude<BirthTimeSource, "" | "legacy_import">, BirthTimeDraftPatch>;

export function BirthTimeIntakeFields({ value, onPatch }: BirthTimeIntakeProps) {
  const groupId = useId();
  const source = value.birthTimeSource;
  const isConfirmed = value.birthTimeStatus === "confirmed";
  const displayState = birthTimeDisplayState(value);
  const knowledgeMode = source === "period_only" || source === "unknown"
    ? "uncertain"
    : source ? "exact" : "";
  const usesClockTime = source === "hospital_record"
    || source === "family_exact"
    || source === "approximate"
    || source === "legacy_import";

  return (
    <div className="birth-time-intake">
      {displayState && (
        <section className="birth-time-profile-result" aria-label="生时校正结果">
          <div className="birth-time-profile-result-heading">
            <span>生时校正结果</span>
            <strong>{displayState.kind === "candidate" ? "候选时间" : "已确认"}</strong>
          </div>
          <dl>
            <div>
              <dt>{displayState.kind === "candidate" ? "待验证候选时间" : "当前排盘时间"}</dt>
              <dd>{displayState.activeTime}</dd>
            </div>
            <div>
              <dt>原始填报</dt>
              <dd>{displayState.reportedLabel}</dd>
            </div>
          </dl>
          {displayState.kind === "candidate" && (
            <p>这仍是未确认候选，不会自动成为出生分钟；{birthTimeConsultationOptionsCopy(value)}</p>
          )}
        </section>
      )}
      <BirthDatePicker
        value={value.date}
        disabled={isConfirmed}
        onChange={(date) => onPatch({ date })}
      />

      {source === "legacy_import" && (
        <p className="birth-time-legacy-note">
          这是账号里已有的确认时间。本阶段保留原始记录，不在资料表内直接覆盖。
        </p>
      )}

      {!isConfirmed && <fieldset className="birth-time-source-fieldset">
        <legend>你是否知道准确出生时间？</legend>
        <div className="birth-time-source-list">
          {birthTimeSourceOptions.map((option) => (
            <label
              className={`birth-time-source-option ${option.value === "family_exact"
                ? knowledgeMode === "exact" ? "is-selected" : ""
                : knowledgeMode === "uncertain" ? "is-selected" : ""}`}
              key={option.value}
            >
              <input
                checked={option.value === "family_exact"
                  ? knowledgeMode === "exact"
                  : knowledgeMode === "uncertain"}
                name={`birth-time-source-${groupId}`}
                type="radio"
                value={option.value}
                onChange={() => onPatch({
                  birthTimeSource: option.value,
                  birthTimeStatus: "reported",
                  time: "",
                  ...sourceDefaults[option.value],
                })}
              />
              <span>
                <b>{option.label}</b>
                <small>{option.hint}</small>
              </span>
            </label>
          ))}
        </div>
      </fieldset>}

      {usesClockTime && (
        <div className="birth-time-detail-grid onboarding-card-reveal">
          <label>
            <span>{isConfirmed ? "当前排盘时间" : source === "approximate" ? "大概时间" : "记录时间"}</span>
            <input
              required
              disabled={isConfirmed}
              type="time"
              value={value.reportedTime || value.time}
              onChange={(event) => onPatch({ reportedTime: event.target.value })}
            />
          </label>
          {source === "hospital_record" && (
            <p className="birth-time-detail-note">系统会无感检查前后 2 分钟的上升与 D9 / D10 稳定性。</p>
          )}
          {source === "approximate" && (
            <label>
              <span>可能误差</span>
              <select
                value={value.uncertaintyBeforeMinutes ?? ""}
                onChange={(event) => {
                  const minutes = Number(event.target.value);
                  onPatch({ uncertaintyBeforeMinutes: minutes, uncertaintyAfterMinutes: minutes });
                }}
              >
                {[15, 30, 60].map((minutes) => (
                  <option key={minutes} value={minutes}>前后 {minutes} 分钟</option>
                ))}
              </select>
            </label>
          )}
        </div>
      )}

      {source === "period_only" && (
        <div className="birth-time-detail-grid onboarding-card-reveal">
          <label>
            <span>请选择最接近的时间范围</span>
            <select
              required
              value={value.birthTimePeriod}
              onChange={(event) => {
                const period = birthTimePeriodOptions.find((option) => option.value === event.target.value);
                if (period) onPatch({ birthTimePeriod: period.value });
              }}
            >
              <option value="" disabled>请选择大致时段</option>
              {birthTimePeriodOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span>补充描述（可选）</span>
            <textarea
              maxLength={240}
              placeholder="例如：天刚亮、午饭前后、家人记得大约 6—8 点"
              rows={2}
              value={value.birthTimeClue}
              onChange={(event) => onPatch({ birthTimeClue: event.target.value })}
            />
          </label>
          <button
            className="button-secondary"
            type="button"
            onClick={() => onPatch({
              birthTimeSource: "unknown",
              reportedTime: "",
              birthTimePeriod: "",
              birthTimeClue: "",
              uncertaintyBeforeMinutes: null,
              uncertaintyAfterMinutes: null,
              birthTimeStatus: "reported",
              time: "",
            })}
          >完全不清楚，跳过出生时间</button>
        </div>
      )}

      {source === "unknown" && (
        <div className="birth-time-detail-note onboarding-card-reveal" role="status">
          <p>已跳过具体出生时间。保存后可以直接使用首页功能，生时校正以后需要时再做。</p>
          <button
            className="button-secondary"
            type="button"
            onClick={() => onPatch({ birthTimeSource: "period_only", birthTimeStatus: "reported" })}
          >我可以描述一个时间范围</button>
        </div>
      )}
    </div>
  );
}
