import { format, isValid, parse } from "date-fns";
import type { JourneySnapshot } from "./birth-time-journey.ts";

const birthDatePattern = "yyyy-MM-dd";
const birthClockPattern = /^(?:[01]\d|2[0-3]):[0-5]\d$/;
const earliestBirthYear = 1900;
const latestBirthYear = 2100;

export type BirthTimeSource =
  | ""
  | "hospital_record"
  | "family_exact"
  | "approximate"
  | "period_only"
  | "unknown"
  | "legacy_import";

export type BirthTimePeriod =
  | ""
  | "early_morning"
  | "morning"
  | "afternoon"
  | "evening"
  | "late_night";

export type BirthTimeStatus =
  | ""
  | "reported"
  | "assessing"
  | "rectifying"
  | "candidate"
  | "confirmed";

export type BirthTimeDraft = {
  readonly date: string;
  readonly time: string;
  readonly reportedTime: string;
  readonly birthTimeSource: BirthTimeSource;
  readonly birthTimePeriod: BirthTimePeriod;
  readonly birthTimeClue: string;
  readonly uncertaintyBeforeMinutes: number | null;
  readonly uncertaintyAfterMinutes: number | null;
  readonly birthTimeStatus: BirthTimeStatus;
};

export type BirthTimeDraftPatch = Partial<BirthTimeDraft>;

export type DeclaredBirthPlace = Readonly<{
  label: string;
  lat: number;
  lon: number;
  tz: number;
}>;

export function parseBirthDate(value: string): Date | undefined {
  if (value === "") return undefined;
  const parsed = parse(value, birthDatePattern, new Date(2000, 0, 1));
  if (!isValid(parsed)
    || format(parsed, birthDatePattern) !== value
    || parsed.getFullYear() < earliestBirthYear
    || parsed.getFullYear() > latestBirthYear) return undefined;
  return parsed;
}

export function isBirthClockTime(value: string): boolean {
  return birthClockPattern.test(value);
}

export function formatBirthDate(value: Date): string {
  return format(value, birthDatePattern);
}

export const birthTimeSourceOptions = [
  { value: "hospital_record", label: "出生证明或医院记录", hint: "先检查前后两分钟是否稳定" },
  { value: "family_exact", label: "家人明确记得具体时间", hint: "进行 5—15 分钟轻量校正" },
  { value: "approximate", label: "只记得大概几点", hint: "按你选择的误差范围扫描" },
  { value: "period_only", label: "只知道早晨、上午、下午或晚上", hint: "先从时段范围做粗筛" },
  { value: "unknown", label: "完全不知道", hint: "不要求你随便填写具体时间" },
] as const;

export const birthTimePeriodOptions = [
  { value: "early_morning", label: "凌晨 / 清晨（04:00—07:59）" },
  { value: "morning", label: "上午（08:00—11:59）" },
  { value: "afternoon", label: "下午（12:00—17:59）" },
  { value: "evening", label: "晚上（18:00—22:59）" },
  { value: "late_night", label: "深夜（23:00—03:59）" },
] as const;

export type BirthTimeDisplayState = {
  readonly kind: "candidate" | "confirmed";
  readonly activeTime: string;
  readonly reportedLabel: string;
};

function reportedBirthTimeLabel(draft: BirthTimeDraft): string {
  if (draft.birthTimeSource === "period_only") {
    return birthTimePeriodOptions.find((option) => option.value === draft.birthTimePeriod)?.label
      ?? "未选择时段";
  }
  if (draft.birthTimeSource === "unknown") return "具体时间未知";
  return draft.reportedTime || draft.time || "尚未填报";
}

export function birthTimeDisplayState(draft: BirthTimeDraft): BirthTimeDisplayState | null {
  if (!draft.time || (draft.birthTimeStatus !== "candidate" && draft.birthTimeStatus !== "confirmed")) {
    return null;
  }
  return {
    kind: draft.birthTimeStatus,
    activeTime: draft.time,
    reportedLabel: reportedBirthTimeLabel(draft),
  };
}

const periodLabels = {
  "": "未选择时段",
  early_morning: "凌晨或清晨",
  morning: "上午",
  afternoon: "下午",
  evening: "晚上",
  late_night: "深夜",
} as const satisfies Record<BirthTimePeriod, string>;

const intentCopy = {
  confirm_stable_record: "医院记录前后两分钟内结构稳定，可以直接作为当前排盘时间。",
  explain_sensitive_boundary: "这个时间靠近敏感边界，需要先做轻量校正，暂不直接排盘。",
  explain_assessment_unavailable: "暂时无法完成稳定性检查，系统不会冒险应用这个具体时间。",
  start_light_rectification: "先用几个高区分度问题检查家人记忆范围。",
  start_standard_rectification: "这个误差范围内存在多个候选，需要先回答几个生活经历问题。",
  start_period_rectification: "已保留你知道的时段，接下来先做粗粒度候选筛选。",
  collect_time_clues: "不会要求你猜一个具体时间，先从家人线索和大致时段开始。",
  continue_rectification_questions: "已记录这条线索，还需要更多证据才能形成候选范围。",
  present_saved_candidate_range: "目前只能保存候选范围，还没有足够证据应用到具体分钟。",
  collect_dated_life_events: "选择题已经完成，请补充几条带日期的关键经历，用于比较实际候选时间。",
  explain_event_evidence_insufficient: "现有事件还不能稳定区分候选时间，可以调整日期或补充其他领域的经历。",
  present_candidate_result: "确定性评分已经形成候选范围，但当前证据只允许保存，不能直接应用。",
  confirm_candidate_time: "候选结果达到应用门槛，仍需你明确确认后才会成为当前排盘时间。",
  confirmed_candidate_time: "候选时间已按你的确认设为当前排盘使用时间。",
} as const satisfies Record<JourneySnapshot["assistantIntent"], string>;

export function assistantIntentCopy(intent: JourneySnapshot["assistantIntent"]) {
  return intentCopy[intent];
}

export function isBirthTimeDraftReady(draft: BirthTimeDraft) {
  if (!parseBirthDate(draft.date) || draft.birthTimeClue.length > 240) return false;
  switch (draft.birthTimeSource) {
    case "hospital_record":
      return isBirthClockTime(draft.reportedTime)
        && draft.uncertaintyBeforeMinutes === 2
        && draft.uncertaintyAfterMinutes === 2;
    case "legacy_import":
      return isBirthClockTime(draft.reportedTime || draft.time);
    case "family_exact":
      return isBirthClockTime(draft.reportedTime)
        && [5, 10, 15].includes(draft.uncertaintyBeforeMinutes ?? -1)
        && draft.uncertaintyBeforeMinutes === draft.uncertaintyAfterMinutes;
    case "approximate":
      return isBirthClockTime(draft.reportedTime)
        && [15, 30, 60].includes(draft.uncertaintyBeforeMinutes ?? -1)
        && draft.uncertaintyBeforeMinutes === draft.uncertaintyAfterMinutes;
    case "period_only":
      return birthTimePeriodOptions.some((option) => option.value === draft.birthTimePeriod)
        && !draft.reportedTime
        && draft.uncertaintyBeforeMinutes === null
        && draft.uncertaintyAfterMinutes === null;
    case "unknown":
      return !draft.reportedTime
        && !draft.birthTimePeriod
        && draft.uncertaintyBeforeMinutes === null
        && draft.uncertaintyAfterMinutes === null;
    case "":
      return false;
    default: {
      const exhaustive: never = draft.birthTimeSource;
      return exhaustive;
    }
  }
}

/**
 * Whether the user has finished declaring what they actually know about birth time.
 * This is an onboarding condition, not a claim that an exact chart minute is ready.
 */
export function isDeclaredBirthProfileComplete(
  draft: BirthTimeDraft,
  place?: DeclaredBirthPlace | null,
) {
  if (!isBirthTimeDraftReady(draft)) return false;
  if (place === undefined) return true;
  return Boolean(place
    && place.label.trim()
    && Number.isFinite(place.lat)
    && place.lat >= -90
    && place.lat <= 90
    && Number.isFinite(place.lon)
    && place.lon >= -180
    && place.lon <= 180
    && Number.isFinite(place.tz)
    && place.tz >= -12
    && place.tz <= 14);
}

export function isBirthTimeReadyForConsultation(draft: BirthTimeDraft) {
  return isBirthClockTime(draft.time)
    && draft.birthTimeStatus === "confirmed";
}

const declaredBirthInputKeys = [
  "date",
  "reportedTime",
  "birthTimeSource",
  "birthTimePeriod",
  "birthTimeClue",
  "uncertaintyBeforeMinutes",
  "uncertaintyAfterMinutes",
] as const satisfies readonly (keyof BirthTimeDraft)[];

export function declaredBirthInputChanged(
  current: BirthTimeDraft,
  next: BirthTimeDraft,
): boolean {
  return declaredBirthInputKeys.some((key) => current[key] !== next[key]);
}

/**
 * Applies an intake edit without allowing a stale, unconfirmed candidate minute
 * to survive changes to the declaration it was calculated from.
 * Confirmed active time belongs to the account and is changed only by explicit
 * rectification confirmation, so ordinary profile edits leave it intact.
 */
export function applyBirthTimeDraftPatch<T extends BirthTimeDraft>(
  current: T,
  patch: BirthTimeDraftPatch,
): T {
  const next = { ...current, ...patch };
  const declarationChanged = declaredBirthInputKeys.some((key) => (
    Object.hasOwn(patch, key) && next[key] !== current[key]
  ));
  if (!declarationChanged || current.birthTimeStatus === "confirmed") return next;
  if (current.birthTimeStatus !== "candidate" && !current.time) return next;
  return {
    ...next,
    time: "",
    birthTimeStatus: "reported",
  } as T;
}

export function birthTimePersistenceValues(draft: BirthTimeDraft) {
  const reportedTime = draft.birthTimeSource === "legacy_import"
    ? draft.reportedTime || draft.time || null
    : draft.birthTimeSource === "hospital_record"
      || draft.birthTimeSource === "family_exact"
      || draft.birthTimeSource === "approximate"
      ? draft.reportedTime || null
      : null;
  const uncertainty = draft.birthTimeSource === "hospital_record"
    ? 2
    : draft.birthTimeSource === "family_exact" || draft.birthTimeSource === "approximate"
      ? draft.uncertaintyBeforeMinutes
      : null;
  return {
    reported_birth_time: reportedTime,
    birth_time_source: draft.birthTimeSource || null,
    birth_time_period: draft.birthTimePeriod || null,
    birth_time_clue: draft.birthTimeClue.trim() || null,
    uncertainty_before_minutes: uncertainty,
    uncertainty_after_minutes: uncertainty,
  };
}

export function describeBirthTimeDraft(draft: BirthTimeDraft) {
  const [year, month, day] = draft.date.split("-").map(Number);
  const date = `${year}年${month}月${day}日`;
  switch (draft.birthTimeSource) {
    case "hospital_record":
      return `${date} ${draft.reportedTime}（医院记录）`;
    case "family_exact":
      return `${date} ${draft.reportedTime}（家人明确记得，前后 ${draft.uncertaintyBeforeMinutes} 分钟）`;
    case "approximate":
      return `${date}，约 ${draft.reportedTime}（前后 ${draft.uncertaintyBeforeMinutes} 分钟）`;
    case "period_only":
      return `${date}，${periodLabels[draft.birthTimePeriod]}`;
    case "unknown":
      return `${date}，具体时间未知`;
    case "legacy_import":
      return `${date} ${draft.reportedTime || draft.time}（既有已确认资料）`;
    case "":
      return date;
    default: {
      const exhaustive: never = draft.birthTimeSource;
      return exhaustive;
    }
  }
}
