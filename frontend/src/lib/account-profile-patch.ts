import { z } from "zod";
import { isBirthClockTime, parseBirthDate } from "./birth-time-intake-model.ts";

const nullableTrimmedString = (maximum: number) => z.string().trim().min(1).max(maximum).nullable();
const nullableBirthDate = z.string().refine((value) => parseBirthDate(value) !== undefined, {
  message: "出生日期必须是真实的 1900—2100 年 ISO 日期",
}).nullable();
const nullableBirthClock = z.string().refine(isBirthClockTime, {
  message: "出生时间必须是 HH:mm",
}).nullable();

const birthTimeSourceSchema = z.enum([
  "hospital_record",
  "family_exact",
  "approximate",
  "period_only",
  "unknown",
  "legacy_import",
]);
const birthTimePeriodSchema = z.enum([
  "early_morning",
  "morning",
  "afternoon",
  "evening",
  "late_night",
]);

export const accountProfilePatchSchema = z.object({
  name: nullableTrimmedString(80).optional(),
  birth_date: nullableBirthDate.optional(),
  // Accepted only for backward-compatible parsing. The account route never
  // writes this client field into active/confirmed birth-time truth.
  birth_time: nullableBirthClock.optional(),
  reported_birth_time: nullableBirthClock.optional(),
  birth_time_source: birthTimeSourceSchema.nullable().optional(),
  birth_time_period: birthTimePeriodSchema.nullable().optional(),
  birth_time_clue: nullableTrimmedString(240).optional(),
  uncertainty_before_minutes: z.number().int().min(0).max(720).nullable().optional(),
  uncertainty_after_minutes: z.number().int().min(0).max(720).nullable().optional(),
  country_code: nullableTrimmedString(8).optional(),
  province_code: nullableTrimmedString(24).optional(),
  city_code: nullableTrimmedString(24).optional(),
  district_code: nullableTrimmedString(24).optional(),
  latitude: z.number().finite().min(-90).max(90).nullable().optional(),
  longitude: z.number().finite().min(-180).max(180).nullable().optional(),
  timezone_offset: z.number().finite().min(-12).max(14).nullable().optional(),
  birth_place_label: nullableTrimmedString(240).optional(),
  birth_place_type: nullableTrimmedString(40).optional(),
  birth_place_provider: z.enum(["geoapify", "china_locations", "mapbox", "geonames"]).nullable().optional(),
  birth_place_provider_id: nullableTrimmedString(160).optional(),
  timezone_id: nullableTrimmedString(80).optional(),
  timezone_source: z.literal("iana_historical").nullable().optional(),
}).strict().superRefine((value, context) => {
  const source = value.birth_time_source;
  const time = value.reported_birth_time;
  const before = value.uncertainty_before_minutes;
  const after = value.uncertainty_after_minutes;
  const addIssue = (path: string, message: string) => context.addIssue({
    code: z.ZodIssueCode.custom,
    path: [path],
    message,
  });

  const declarationKeys = [
    "birth_date",
    "reported_birth_time",
    "birth_time_source",
    "birth_time_period",
    "birth_time_clue",
    "uncertainty_before_minutes",
    "uncertainty_after_minutes",
  ] as const;
  const mutatesDeclaration = declarationKeys.some((key) => value[key] !== undefined);
  const coordinateCount = [value.latitude, value.longitude].filter((coordinate) => coordinate != null).length;
  if (coordinateCount === 1) {
    addIssue("latitude", "出生地点经纬度必须完整提交");
  }
  const globalLocationFields = [
    value.birth_place_label,
    value.birth_place_type,
    value.birth_place_provider,
    value.birth_place_provider_id,
    value.timezone_id,
    value.timezone_source,
  ];
  const hasGlobalLocation = globalLocationFields.some((field) => field != null);
  if (hasGlobalLocation && (coordinateCount !== 2 || !value.timezone_id)) {
    addIssue("timezone_id", "全球出生地点必须包含完整坐标与 IANA 时区");
  }
  if (source === undefined) {
    if (mutatesDeclaration) addIssue("birth_time_source", "修改出生资料时必须同时说明时间来源");
    return;
  }
  if (source === null) {
    if (value.birth_date !== undefined && value.birth_date !== null) {
      addIssue("birth_time_source", "填写出生日期后必须说明时间来源");
    }
    if (time || value.birth_time || value.birth_time_period || value.birth_time_clue
      || before != null || after != null) {
      addIssue("birth_time_source", "未选择时间来源时不得提交时间或误差范围");
    }
    return;
  }
  if (!value.birth_date) addIssue("birth_date", "出生时间声明必须包含真实出生日期");
  if (source !== "legacy_import" && value.birth_time) {
    addIssue("birth_time", "只有既有资料迁移可以提交兼容时间字段");
  }

  const ensureNoPeriod = () => {
    if (value.birth_time_period) addIssue("birth_time_period", "具体时间来源不得同时提交时段");
  };
  const ensureNoUncertainty = () => {
    if (before != null || after != null) {
      addIssue("uncertainty_before_minutes", "该时间来源不得提交误差范围");
    }
  };

  if (source === "hospital_record") {
    if (!time) addIssue("reported_birth_time", "医院记录需要具体时间");
    if (before !== 2 || after !== 2) addIssue("uncertainty_before_minutes", "医院记录固定检查前后 2 分钟");
    ensureNoPeriod();
  } else if (source === "family_exact") {
    if (!time) addIssue("reported_birth_time", "家人记忆需要具体时间");
    if (![5, 10, 15].includes(before ?? -1) || before !== after) {
      addIssue("uncertainty_before_minutes", "家人记忆误差必须为前后 5、10 或 15 分钟");
    }
    ensureNoPeriod();
  } else if (source === "approximate") {
    if (!time) addIssue("reported_birth_time", "大概时间需要具体 HH:mm");
    if (![15, 30, 60].includes(before ?? -1) || before !== after) {
      addIssue("uncertainty_before_minutes", "大概时间误差必须为前后 15、30 或 60 分钟");
    }
    ensureNoPeriod();
  } else if (source === "legacy_import") {
    if (!time && !value.birth_time) addIssue("reported_birth_time", "既有资料需要具体时间");
    ensureNoPeriod();
    ensureNoUncertainty();
  } else if (source === "period_only") {
    if (!value.birth_time_period) addIssue("birth_time_period", "只知道时段时必须选择时段");
    if (time) addIssue("reported_birth_time", "只知道时段时不得同时提交具体分钟");
    ensureNoUncertainty();
  } else if (source === "unknown") {
    if (time) addIssue("reported_birth_time", "时间未知时不得提交具体分钟");
    if (value.birth_time_period) addIssue("birth_time_period", "时间未知时不得提交确定时段");
    ensureNoUncertainty();
  }

});

export type AccountProfilePatch = z.infer<typeof accountProfilePatchSchema>;

type AccountBirthTimeState = Readonly<{
  birth_date: string | null;
  reported_birth_time: string | null;
  birth_time_source: string | null;
  birth_time_period: string | null;
  birth_time_clue: string | null;
  uncertainty_before_minutes: number | null;
  uncertainty_after_minutes: number | null;
  active_birth_time: string | null;
  birth_time: string | null;
  birth_time_status: string | null;
  rectification_case_id: string | null;
  country_code?: string | null;
  province_code?: string | null;
  city_code?: string | null;
  district_code?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  timezone_offset?: number | null;
  birth_place_label?: string | null;
  birth_place_type?: string | null;
  birth_place_provider?: string | null;
  birth_place_provider_id?: string | null;
  timezone_id?: string | null;
  timezone_source?: string | null;
}>;

const declarationFields = [
  "birth_date",
  "reported_birth_time",
  "birth_time_source",
  "birth_time_period",
  "birth_time_clue",
  "uncertainty_before_minutes",
  "uncertainty_after_minutes",
  "country_code",
  "province_code",
  "city_code",
  "district_code",
  "latitude",
  "longitude",
  "timezone_offset",
  "birth_place_label",
  "birth_place_type",
  "birth_place_provider",
  "birth_place_provider_id",
  "timezone_id",
  "timezone_source",
] as const;

const concurrencyFields = [
  ...declarationFields,
  "active_birth_time",
  "birth_time",
  "birth_time_status",
  "rectification_case_id",
] as const;

type ConditionalProfileQuery<Query> = Readonly<{
  eq: (column: string, value: string | number) => Query;
  is: (column: string, value: null) => Query;
}>;

/** Keeps an ordinary profile edit from overwriting a concurrent edit or confirmation. */
export function applyAccountProfileConcurrencyGuards<
  Query extends ConditionalProfileQuery<Query>,
>(query: Query, current: AccountBirthTimeState): Query {
  let guarded = query;
  for (const field of concurrencyFields) {
    const value = current[field];
    if (value === undefined) continue;
    guarded = value === null
      ? guarded.is(field, null)
      : guarded.eq(field, value);
  }
  return guarded;
}

export type AccountBirthTimeApplicationPatch = Readonly<{
  active_birth_time?: null;
  birth_time?: null;
  birth_time_status?: "reported";
  rectification_case_id?: null;
}>;

export function resolveAccountBirthTimeApplicationPatch(
  current: AccountBirthTimeState,
  patch: AccountProfilePatch,
): AccountBirthTimeApplicationPatch {
  const declarationChanged = declarationFields.some((field) => (
    patch[field] !== undefined && patch[field] !== current[field]
  ));
  if (!declarationChanged) return {};

  const confirmed = current.birth_time_status === "confirmed"
    || (current.birth_time_status === null && isBirthClockTime(current.birth_time ?? ""));
  if (confirmed) return {};
  return {
    active_birth_time: null,
    birth_time: null,
    birth_time_status: "reported",
    rectification_case_id: null,
  };
}
