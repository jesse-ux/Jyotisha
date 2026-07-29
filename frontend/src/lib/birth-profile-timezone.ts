type RecordValue = Record<string, unknown>;

export class BirthProfileTimezoneError extends Error {
  constructor() {
    super("Unable to resolve historical birth timezone offset");
    this.name = "BirthProfileTimezoneError";
  }
}

function record(value: unknown): RecordValue | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as RecordValue
    : null;
}

function valueFor(profile: RecordValue, snakeKey: string, camelKey: string): unknown {
  return profile[snakeKey] ?? profile[camelKey];
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function calendarDate(value: unknown): string | null {
  if (value instanceof Date && !Number.isNaN(value.getTime())) return value.toISOString().slice(0, 10);
  return text(value);
}

export function finiteBirthNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function durableBirthCoordinate(value: unknown): number | null {
  const coordinate = finiteBirthNumber(value);
  if (coordinate === null) return null;
  const rounded = Math.round(coordinate * 1_000_000) / 1_000_000;
  return Object.is(rounded, -0) ? 0 : rounded;
}

export function birthProfileReferenceTime(value: unknown, preferredTime?: string | null): string {
  const preferred = text(preferredTime)?.slice(0, 5);
  if (preferred && /^([01]\d|2[0-3]):[0-5]\d$/.test(preferred)) return preferred;
  const profile = record(value);
  const reported = text(profile ? valueFor(profile, "reported_birth_time", "reportedTime") : null)?.slice(0, 5);
  if (reported && /^([01]\d|2[0-3]):[0-5]\d$/.test(reported)) return reported;
  const direct = text(profile ? valueFor(profile, "birth_time", "time") : null)?.slice(0, 5);
  if (direct && /^([01]\d|2[0-3]):[0-5]\d$/.test(direct)) return direct;
  const period = text(profile ? valueFor(profile, "birth_time_period", "birthTimePeriod") : null);
  return {
    early_morning: "06:00",
    morning: "10:00",
    afternoon: "15:00",
    evening: "20:30",
    late_night: "23:30",
  }[period ?? ""] ?? "12:00";
}

type ResolveBirthTimezoneOptions = Readonly<{
  fetchImpl?: typeof fetch;
  apiBase?: string;
  preferredTime?: string | null;
}>;

export async function resolveMissingBirthTimezoneOffset(
  value: unknown,
  options: ResolveBirthTimezoneOptions = {},
): Promise<unknown> {
  const profile = record(value);
  if (!profile) return value;
  const existingOffset = finiteBirthNumber(valueFor(profile, "timezone_offset", "timezoneOffset"));
  if (existingOffset !== null) return value;
  const latitude = finiteBirthNumber(profile.latitude);
  const longitude = finiteBirthNumber(profile.longitude);
  const birthDate = calendarDate(valueFor(profile, "birth_date", "date"));
  const timezoneId = text(valueFor(profile, "timezone_id", "timezoneId"));
  if (latitude === null || longitude === null || !birthDate || !timezoneId) return value;

  const fetchImpl = options.fetchImpl ?? fetch;
  const apiBase = options.apiBase ?? process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200";
  let response: Response;
  try {
    response = await fetchImpl(`${apiBase}/api/location/timezone`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        latitude,
        longitude,
        birthDate,
        birthTime: birthProfileReferenceTime(profile, options.preferredTime),
      }),
      cache: "no-store",
    });
  } catch {
    throw new BirthProfileTimezoneError();
  }
  if (!response.ok) throw new BirthProfileTimezoneError();
  const payload = record(await response.json().catch(() => null));
  const timezoneOffset = finiteBirthNumber(payload?.timezoneOffset);
  if (payload?.available !== true || timezoneOffset === null) {
    throw new BirthProfileTimezoneError();
  }
  return {
    ...profile,
    timezone_offset: timezoneOffset,
    timezoneOffset,
  };
}
