import { chinaLocations } from "../data/china-locations.ts";
import { isBirthClockTime, parseBirthDate } from "./birth-time-intake-model.ts";
import { resolveMissingBirthTimezoneOffset } from "./birth-profile-timezone.ts";
import type { ConsultationBirthTimeMode } from "./consultation-birth-time-mode.ts";

export type ConsultationProfileTruthErrorCode =
  | "profile_unavailable"
  | "profile_incomplete"
  | "profile_inconsistent"
  | "mode_changed";

export class ConsultationProfileTruthError extends Error {
  readonly code: ConsultationProfileTruthErrorCode;

  constructor(code: ConsultationProfileTruthErrorCode) {
    super(`Consultation profile truth rejected: ${code}`);
    this.name = "ConsultationProfileTruthError";
    this.code = code;
  }
}

type ServerChartToolInput = Readonly<{
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  city: string;
  lat: number;
  lon: number;
  tz: number;
}>;

export type ServerChartConsultation = Readonly<{
  name: string;
  toolInput: ServerChartToolInput;
  truth: Readonly<{
    birthDate: string;
    reportedBirthTime: string | null;
    activeBirthTime: string | null;
    selectedTimeKind: "reported" | "active" | "candidate_range_boundary";
    birthTimeSource: string;
    birthTimeStatus: string;
    placeLabel: string;
    placeCodes: Readonly<{
      countryCode: string | null;
      provinceCode: string | null;
      cityCode: string | null;
      districtCode: string | null;
    }>;
    placeId: string | null;
    placeType: string | null;
    placeProvider: string | null;
    timezoneId: string | null;
    timezoneSource: string | null;
    latitude: number;
    longitude: number;
    timezoneOffset: number;
  }>;
}>;

type PrepareConsultationRouteInput<Reservation> = Readonly<{
  userId: string;
  mode: ConsultationBirthTimeMode;
  candidateRange?: Readonly<{ start: string; end: string }>;
  loadProfile: (userId: string) => Promise<unknown>;
  resolveTimezoneOffset?: (profile: unknown, selectedTime?: string) => Promise<unknown>;
  reserve: () => Promise<Reservation>;
}>;

type RecordValue = Record<string, unknown>;

const allowedBirthTimeSources = new Set([
  "hospital_record", "family_exact", "approximate", "period_only", "unknown", "legacy_import",
]);
const allowedBirthTimeStatuses = new Set([
  "reported", "assessing", "rectifying", "candidate", "confirmed",
]);
const concreteReportedSources = new Set([
  "hospital_record", "family_exact", "approximate",
]);

function record(value: unknown): RecordValue | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as RecordValue
    : null;
}

function requiredText(profile: RecordValue, key: string): string {
  const value = profile[key];
  if (typeof value !== "string" || !value.trim()) {
    throw new ConsultationProfileTruthError("profile_incomplete");
  }
  return value.trim();
}

function nullableClock(profile: RecordValue, key: string): string | null {
  const value = profile[key];
  if (value === null || value === undefined) return null;
  if (typeof value !== "string") {
    throw new ConsultationProfileTruthError("profile_inconsistent");
  }
  const clock = value.slice(0, 5);
  if (!isBirthClockTime(clock)) {
    throw new ConsultationProfileTruthError("profile_inconsistent");
  }
  return clock;
}

function requiredFiniteNumber(profile: RecordValue, key: string, minimum: number, maximum: number) {
  const value = profile[key];
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new ConsultationProfileTruthError("profile_incomplete");
  }
  if (value < minimum || value > maximum) {
    throw new ConsultationProfileTruthError("profile_inconsistent");
  }
  return value;
}

function optionalText(profile: RecordValue, key: string): string | null {
  const value = profile[key];
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function persistedChartMode(value: unknown): Exclude<ConsultationBirthTimeMode, "general_no_birth_time"> | null {
  const profile = record(value);
  if (!profile) return null;
  const status = optionalText(profile, "birth_time_status");
  const source = optionalText(profile, "birth_time_source");
  const activeTime = optionalText(profile, "active_birth_time")?.slice(0, 5) ?? "";
  const reportedTime = optionalText(profile, "reported_birth_time")?.slice(0, 5) ?? "";
  if (status === "confirmed" && isBirthClockTime(activeTime)) return "verified_chart";
  if (status && allowedBirthTimeStatuses.has(status) && status !== "confirmed"
    && source && concreteReportedSources.has(source)
    && isBirthClockTime(reportedTime)) return "unverified_birth_time";
  return null;
}

function legacyChinaPlaceLabel(profile: RecordValue): string | null {
  const countryCode = optionalText(profile, "country_code");
  const provinceCode = optionalText(profile, "province_code");
  const cityCode = optionalText(profile, "city_code");
  const districtCode = optionalText(profile, "district_code");
  const country = chinaLocations.country;
  if (countryCode !== country.code || !provinceCode || !cityCode) return null;
  const province = country.provinces.find((candidate) => candidate.code === provinceCode);
  const city = province?.cities.find((candidate) => candidate.code === cityCode);
  const district = districtCode
    ? city?.districts.find((candidate) => candidate.code === districtCode)
    : undefined;
  if (!province || !city || (districtCode && !district)) return null;
  return [country.name, province.name, city.name, district?.name]
    .filter((label, index, labels) => Boolean(label) && labels.indexOf(label) === index)
    .join(" · ");
}

function serverChartFromProfile(
  value: unknown,
  mode: Exclude<ConsultationBirthTimeMode, "general_no_birth_time">,
  candidateBoundary?: string,
): ServerChartConsultation {
  const profile = record(value);
  if (!profile) throw new ConsultationProfileTruthError("profile_incomplete");

  const name = requiredText(profile, "name");
  if (name.length > 80) throw new ConsultationProfileTruthError("profile_inconsistent");
  const birthDate = requiredText(profile, "birth_date");
  if (!parseBirthDate(birthDate)) {
    throw new ConsultationProfileTruthError("profile_inconsistent");
  }
  const [year, month, day] = birthDate.split("-").map(Number);
  const reportedBirthTime = nullableClock(profile, "reported_birth_time");
  const activeBirthTime = nullableClock(profile, "active_birth_time");
  const birthTimeSource = requiredText(profile, "birth_time_source");
  const birthTimeStatus = requiredText(profile, "birth_time_status");
  if (!allowedBirthTimeSources.has(birthTimeSource)
    || !allowedBirthTimeStatuses.has(birthTimeStatus)) {
    throw new ConsultationProfileTruthError("profile_inconsistent");
  }

  const countryCode = optionalText(profile, "country_code");
  const provinceCode = optionalText(profile, "province_code");
  const cityCode = optionalText(profile, "city_code");
  const districtCode = optionalText(profile, "district_code");
  const placeId = optionalText(profile, "birth_place_provider_id");
  const placeType = optionalText(profile, "birth_place_type");
  const placeProvider = optionalText(profile, "birth_place_provider");
  const timezoneId = optionalText(profile, "timezone_id");
  const timezoneSource = optionalText(profile, "timezone_source");
  const latitude = requiredFiniteNumber(profile, "latitude", -90, 90);
  const longitude = requiredFiniteNumber(profile, "longitude", -180, 180);
  const timezoneOffset = requiredFiniteNumber(profile, "timezone_offset", -12, 14);
  const placeLabel = optionalText(profile, "birth_place_label")
    ?? legacyChinaPlaceLabel(profile)
    ?? placeId;
  if (!placeLabel) throw new ConsultationProfileTruthError("profile_incomplete");

  let selectedTime: string;
  let selectedTimeKind: "reported" | "active" | "candidate_range_boundary";
  if (candidateBoundary !== undefined) {
    if (!isBirthClockTime(candidateBoundary)) {
      throw new ConsultationProfileTruthError("profile_inconsistent");
    }
    selectedTime = candidateBoundary;
    selectedTimeKind = "candidate_range_boundary";
  } else if (mode === "verified_chart") {
    if (birthTimeStatus !== "confirmed") {
      throw new ConsultationProfileTruthError("mode_changed");
    }
    if (!activeBirthTime) throw new ConsultationProfileTruthError("profile_incomplete");
    selectedTime = activeBirthTime;
    selectedTimeKind = "active";
  } else {
    if (birthTimeStatus === "confirmed" || !concreteReportedSources.has(birthTimeSource)) {
      throw new ConsultationProfileTruthError("mode_changed");
    }
    if (!reportedBirthTime) throw new ConsultationProfileTruthError("profile_incomplete");
    selectedTime = reportedBirthTime;
    selectedTimeKind = "reported";
  }
  const [hour, minute] = selectedTime.split(":").map(Number);

  return Object.freeze({
    name,
    toolInput: Object.freeze({
      year,
      month,
      day,
      hour,
      minute,
      city: placeLabel,
      lat: latitude,
      lon: longitude,
      tz: timezoneOffset,
    }),
    truth: Object.freeze({
      birthDate,
      reportedBirthTime,
      activeBirthTime,
      selectedTimeKind,
      birthTimeSource,
      birthTimeStatus,
      placeLabel,
      placeCodes: Object.freeze({
        countryCode,
        provinceCode,
        cityCode,
        districtCode,
      }),
      placeId,
      placeType,
      placeProvider,
      timezoneId,
      timezoneSource,
      latitude,
      longitude,
      timezoneOffset,
    }),
  });
}

/**
 * The route's pre-billing service boundary. Chart modes must load and resolve
 * account truth successfully before the reservation callback can run.
 */
export async function prepareConsultationRoute<Reservation>(
  input: PrepareConsultationRouteInput<Reservation>,
) {
  let profile: unknown;
  try {
    profile = await input.loadProfile(input.userId);
  } catch (error) {
    if (input.mode === "general_no_birth_time" && !input.candidateRange) profile = null;
    else if (error instanceof ConsultationProfileTruthError) throw error;
    else throw new ConsultationProfileTruthError("profile_unavailable");
  }

  const consultationMode = input.candidateRange
    ? "unverified_birth_time"
    : input.mode === "general_no_birth_time"
      ? persistedChartMode(profile) ?? input.mode
      : input.mode;
  let serverChart: ServerChartConsultation | null = null;
  if (consultationMode !== "general_no_birth_time") {
    const profileValue = record(profile);
    if (input.candidateRange && (!isBirthClockTime(input.candidateRange.start)
      || !isBirthClockTime(input.candidateRange.end))) {
      throw new ConsultationProfileTruthError("profile_inconsistent");
    }
    const selectedTime = input.candidateRange?.start ?? (consultationMode === "verified_chart"
      ? nullableClock(profileValue ?? {}, "active_birth_time")
      : nullableClock(profileValue ?? {}, "reported_birth_time"));
    try {
      profile = await (input.resolveTimezoneOffset ?? ((value, time) => (
        resolveMissingBirthTimezoneOffset(value, { preferredTime: time })
      )))(profile, selectedTime ?? undefined);
    } catch {
      throw new ConsultationProfileTruthError("profile_unavailable");
    }
    serverChart = serverChartFromProfile(
      profile,
      consultationMode,
      input.candidateRange?.start,
    );
  }
  const reservation = await input.reserve();
  return Object.freeze({ consultationMode, serverChart, reservation });
}
