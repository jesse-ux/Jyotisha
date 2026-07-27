import { chinaLocations } from "../data/china-locations.ts";
import type { AccountRectificationCaseState } from "./birth-time-consultation-consent.ts";
import {
  declaredBirthInputSchema,
  type DeclaredBirthInput,
} from "./conversational-rectification/persistence-contracts.ts";
import { durableBirthCoordinate } from "./birth-profile-timezone.ts";

type RecordValue = Record<string, unknown>;

const unfinishedStatuses = new Set<AccountRectificationCaseState["status"]>([
  "starting",
  "active",
  "paused",
  "confirming",
]);

function record(value: unknown): RecordValue | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as RecordValue
    : null;
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function clock(value: unknown): string | null {
  const normalized = text(value)?.slice(0, 5) ?? null;
  return normalized && /^([01]\d|2[0-3]):[0-5]\d$/.test(normalized)
    ? normalized
    : null;
}

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function integer(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) ? value : null;
}

function currentDeclaration(value: unknown, fallbackTimezoneOffset?: number): DeclaredBirthInput | null {
  const profile = record(value);
  if (!profile) return null;
  const birthDate = text(profile.birth_date);
  const source = text(profile.birth_time_source);
  const cityCode = text(profile.city_code);
  const city = text(profile.birth_place_label);
  const placeId = text(profile.birth_place_provider_id);
  const latitude = durableBirthCoordinate(profile.latitude);
  const longitude = durableBirthCoordinate(profile.longitude);
  const timezoneOffset = finiteNumber(profile.timezone_offset) ?? fallbackTimezoneOffset ?? null;
  if (!birthDate || !source || (!city && !cityCode && !placeId)
    || latitude === null || longitude === null
    || timezoneOffset === null) return null;

  const birthplace = {
    ...(city ? { city } : {}),
    ...(placeId ? { placeId } : {}),
    ...(text(profile.birth_place_type) ? { placeType: text(profile.birth_place_type) } : {}),
    ...(text(profile.birth_place_provider) ? { provider: text(profile.birth_place_provider) } : {}),
    ...(text(profile.country_code) ? { countryCode: text(profile.country_code) } : {}),
    ...(text(profile.province_code) ? { provinceCode: text(profile.province_code) } : {}),
    ...(cityCode ? { cityCode } : {}),
    ...(text(profile.district_code) ? { districtCode: text(profile.district_code) } : {}),
    latitude,
    longitude,
    ...(text(profile.timezone_id) ? { timezoneId: text(profile.timezone_id) } : {}),
    ...(text(profile.timezone_source) ? { timezoneSource: text(profile.timezone_source) } : {}),
    timezoneOffset,
  };
  const common = {
    birthDate,
    birthTimeClue: text(profile.birth_time_clue),
    birthplace,
  };
  const reportedTime = clock(profile.reported_birth_time);
  const reportedPeriod = text(profile.birth_time_period);
  const uncertaintyBeforeMinutes = integer(profile.uncertainty_before_minutes);
  const uncertaintyAfterMinutes = integer(profile.uncertainty_after_minutes);
  let input: unknown;
  switch (source) {
    case "hospital_record":
    case "family_exact":
    case "approximate":
      input = {
        ...common,
        source,
        reportedTime,
        uncertaintyBeforeMinutes,
        uncertaintyAfterMinutes,
      };
      break;
    case "period_only":
      input = { ...common, source, reportedPeriod };
      break;
    case "unknown":
      input = { ...common, source };
      break;
    case "legacy_import":
      input = {
        ...common,
        source,
        ...(reportedTime ? { reportedTime } : {}),
        ...(reportedPeriod ? { reportedPeriod } : {}),
        ...(uncertaintyBeforeMinutes === null ? {} : { uncertaintyBeforeMinutes }),
        ...(uncertaintyAfterMinutes === null ? {} : { uncertaintyAfterMinutes }),
      };
      break;
    default:
      return null;
  }
  const parsed = declaredBirthInputSchema.safeParse(input);
  return parsed.success ? parsed.data : null;
}

function canonicalPlaceLabel(input: DeclaredBirthInput): string | null {
  const place = input.birthplace;
  if (place.city) return place.city;
  const country = chinaLocations.country;
  if (place.countryCode !== country.code || !place.provinceCode || !place.cityCode) return null;
  const province = country.provinces.find((candidate) => candidate.code === place.provinceCode);
  const city = province?.cities.find((candidate) => candidate.code === place.cityCode);
  const district = place.districtCode
    ? city?.districts.find((candidate) => candidate.code === place.districtCode)
    : undefined;
  if (!province || !city || (place.districtCode && !district)) return null;
  return [country.name, province.name, city.name, district?.name]
    .filter((label, index, labels) => Boolean(label) && labels.indexOf(label) === index)
    .join(" · ");
}

function withoutBirthplace(input: DeclaredBirthInput): unknown {
  const declaration: Record<string, unknown> = { ...input };
  delete declaration.birthplace;
  return declaration;
}

function sameJson(left: unknown, right: unknown): boolean {
  if (Object.is(left, right)) return true;
  if (Array.isArray(left) || Array.isArray(right)) {
    return Array.isArray(left) && Array.isArray(right)
      && left.length === right.length
      && left.every((value, index) => sameJson(value, right[index]));
  }
  const leftRecord = record(left);
  const rightRecord = record(right);
  if (!leftRecord || !rightRecord) return false;
  const leftKeys = Object.keys(leftRecord).sort();
  const rightKeys = Object.keys(rightRecord).sort();
  return leftKeys.length === rightKeys.length
    && leftKeys.every((key, index) => key === rightKeys[index]
      && sameJson(leftRecord[key], rightRecord[key]));
}

function declarationMatches(current: DeclaredBirthInput, stored: DeclaredBirthInput) {
  if (!sameJson(withoutBirthplace(current), withoutBirthplace(stored))) {
    return false;
  }
  const currentPlace = current.birthplace as Record<string, unknown>;
  const storedPlace = stored.birthplace as Record<string, unknown>;
  for (const [key, value] of Object.entries(storedPlace)) {
    if (key === "city") continue;
    if (!sameJson(currentPlace[key], value)) return false;
  }
  if (!stored.birthplace.city) return true;
  return stored.birthplace.city === canonicalPlaceLabel(current);
}

function project(row: RecordValue): AccountRectificationCaseState | null {
  const status = typeof row.status === "string"
    && unfinishedStatuses.has(row.status as AccountRectificationCaseState["status"])
    ? row.status as AccountRectificationCaseState["status"]
    : null;
  if (typeof row.id !== "string"
    || row.journey_protocol !== "conversational-evidence-v3"
    || !status
    || typeof row.turn_version !== "number"
    || !Number.isSafeInteger(row.turn_version)
    || row.turn_version < 0) return null;
  return Object.freeze({
    caseId: row.id,
    journeyProtocol: "conversational-evidence-v3" as const,
    status,
    turnVersion: row.turn_version,
    isRevision: typeof row.revision_of_case_id === "string",
    preservesActiveTime: typeof row.baseline_active_time === "string",
  });
}

/** Selects the latest loaded unfinished case that belongs to this declaration. */
export function resolveAccountRectificationCase(
  profile: unknown,
  rows: readonly unknown[],
): AccountRectificationCaseState | null {
  for (const value of rows) {
    const row = record(value);
    if (!row) continue;
    const projected = project(row);
    if (!projected) continue;
    const declared = declaredBirthInputSchema.safeParse(row.declared_birth_input);
    if (!declared.success) continue;
    const current = currentDeclaration(profile, declared.data.birthplace.timezoneOffset);
    if (current && declarationMatches(current, declared.data)) return projected;
  }
  return null;
}


const unfinishedV4Statuses = new Set<AccountRectificationCaseState["status"]>([
  "awaiting_answer", "processing", "range_ready", "paused",
]);

/** V4 cases already carry the calculation spec; creation atomically replaces a stale spec. */
export function resolveAccountRectificationV4Case(rows: readonly unknown[]): AccountRectificationCaseState | null {
  for (const value of rows) {
    const row = record(value);
    if (!row || typeof row.id !== "string" || typeof row.version !== "number"
      || !Number.isSafeInteger(row.version) || row.version < 0
      || typeof row.status !== "string"
      || !unfinishedV4Statuses.has(row.status as AccountRectificationCaseState["status"])
      || row.accepted_range_start !== null) continue;
    return Object.freeze({
      caseId: row.id,
      journeyProtocol: "rectification-evidence-v4" as const,
      status: row.status as AccountRectificationCaseState["status"],
      turnVersion: row.version,
      isRevision: false,
      preservesActiveTime: true,
    });
  }
  return null;
}
