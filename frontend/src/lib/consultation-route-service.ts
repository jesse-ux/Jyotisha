import { chinaLocations } from "../data/china-locations.ts";
import { isBirthClockTime, parseBirthDate } from "./birth-time-intake-model.ts";
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
    selectedTimeKind: "reported" | "active";
    birthTimeSource: string;
    birthTimeStatus: string;
    placeLabel: string;
    placeCodes: Readonly<{
      countryCode: string;
      provinceCode: string;
      cityCode: string;
      districtCode: string | null;
    }>;
    latitude: number;
    longitude: number;
    timezoneOffset: number;
  }>;
}>;

type PrepareConsultationRouteInput<Reservation> = Readonly<{
  userId: string;
  mode: ConsultationBirthTimeMode;
  loadProfile: (userId: string) => Promise<unknown>;
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

function sameCoordinate(left: number, right: number) {
  return Math.abs(left - right) <= 0.000001;
}

function serverChartFromProfile(
  value: unknown,
  mode: Exclude<ConsultationBirthTimeMode, "general_no_birth_time">,
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

  const countryCode = requiredText(profile, "country_code");
  const provinceCode = requiredText(profile, "province_code");
  const cityCode = requiredText(profile, "city_code");
  const districtValue = profile.district_code;
  const districtCode = typeof districtValue === "string" && districtValue.trim()
    ? districtValue.trim()
    : null;
  const latitude = requiredFiniteNumber(profile, "latitude", -90, 90);
  const longitude = requiredFiniteNumber(profile, "longitude", -180, 180);
  const timezoneOffset = requiredFiniteNumber(profile, "timezone_offset", -12, 14);

  const country = chinaLocations.country;
  const province = country.provinces.find((candidate) => candidate.code === provinceCode);
  const city = province?.cities.find((candidate) => candidate.code === cityCode);
  const district = districtCode
    ? city?.districts.find((candidate) => candidate.code === districtCode)
    : undefined;
  if (countryCode !== country.code || !province || !city
    || (city.districts.length > 0 && !district)
    || (districtCode !== null && !district)) {
    throw new ConsultationProfileTruthError("profile_inconsistent");
  }
  const location = district ?? city;
  if (!sameCoordinate(latitude, location.center[1])
    || !sameCoordinate(longitude, location.center[0])
    || !sameCoordinate(timezoneOffset, country.timezone)) {
    throw new ConsultationProfileTruthError("profile_inconsistent");
  }
  const placeLabel = [country.name, province.name, city.name, district?.name]
    .filter((label, index, labels) => Boolean(label) && labels.indexOf(label) === index)
    .join(" · ");

  let selectedTime: string;
  let selectedTimeKind: "reported" | "active";
  if (mode === "verified_chart") {
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
  let serverChart: ServerChartConsultation | null = null;
  if (input.mode !== "general_no_birth_time") {
    let profile: unknown;
    try {
      profile = await input.loadProfile(input.userId);
    } catch (error) {
      if (error instanceof ConsultationProfileTruthError) throw error;
      throw new ConsultationProfileTruthError("profile_unavailable");
    }
    serverChart = serverChartFromProfile(profile, input.mode);
  }
  const reservation = await input.reserve();
  return Object.freeze({ serverChart, reservation });
}
