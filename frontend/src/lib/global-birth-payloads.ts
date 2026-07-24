import { chinaLocations } from "@/data/china-locations";
import { finiteBirthNumber, resolveMissingBirthTimezoneOffset } from "@/lib/birth-profile-timezone";

export type GlobalBirthProfile = {
  name?: string;
  date?: string;
  time?: string;
  countryCode?: string;
  provinceCode?: string;
  cityCode?: string;
  districtCode?: string;
  latitude?: number | null;
  longitude?: number | null;
  timezoneId?: string;
  timezoneOffset?: number | null;
};

function resolvedLocation(profile: GlobalBirthProfile) {
  const province = chinaLocations.country.provinces.find((item) => item.code === profile.provinceCode);
  const city = province?.cities.find((item) => item.code === profile.cityCode);
  return city?.districts.find((item) => item.code === profile.districtCode) ?? city;
}

export async function dailyProfilePayload(profile: GlobalBirthProfile, today: string) {
  if (!profile.date || !profile.time) return null;
  const resolved = await resolveMissingBirthTimezoneOffset(profile, {
    preferredTime: profile.time,
  }) as GlobalBirthProfile;
  const [year, month, day] = profile.date.split("-").map(Number);
  const [hour, minute] = profile.time.split(":").map(Number);
  const location = resolvedLocation(profile);
  const lat = finiteBirthNumber(resolved.latitude) ?? location?.center[1] ?? null;
  const lon = finiteBirthNumber(resolved.longitude) ?? location?.center[0] ?? null;
  const tz = finiteBirthNumber(resolved.timezoneOffset)
    ?? (location ? chinaLocations.country.timezone : null);
  if (!year || !month || !day || Number.isNaN(hour) || Number.isNaN(minute)
    || lat === null || lon === null || tz === null) return null;
  return {
    year,
    month,
    day,
    hour,
    minute,
    lat,
    lon,
    tz,
    transit_date: today,
    today,
    ayanamsa: "lahiri",
    node_mode: "mean",
  };
}

export async function synastryBirthPayload(profile: GlobalBirthProfile) {
  const resolved = await resolveMissingBirthTimezoneOffset(profile, {
    preferredTime: profile.time,
  }) as GlobalBirthProfile;
  const [year, month, day] = String(profile.date || "").split("-").map(Number);
  const [hour, minute] = String(profile.time || "").split(":").map(Number);
  const location = resolvedLocation(profile);
  const lat = finiteBirthNumber(resolved.latitude) ?? location?.center[1] ?? null;
  const lon = finiteBirthNumber(resolved.longitude) ?? location?.center[0] ?? null;
  const tz = finiteBirthNumber(resolved.timezoneOffset)
    ?? (location ? chinaLocations.country.timezone : null);
  if (![year, month, day, hour, minute].every(Number.isFinite)
    || lat === null || lon === null || tz === null) {
    throw new Error("birth_profile_incomplete");
  }
  return {
    year,
    month,
    day,
    hour,
    minute,
    second: 0,
    lat,
    lon,
    tz,
  };
}
