import { chinaLocations } from "@/data/china-locations";
import { finiteBirthNumber, resolveMissingBirthTimezoneOffset } from "@/lib/birth-profile-timezone";

export type BirthRectificationProfile = {
  date?: string;
  time?: string;
  provinceCode?: string;
  cityCode?: string;
  districtCode?: string;
  latitude?: number | null;
  longitude?: number | null;
  timezoneId?: string;
  timezoneOffset?: number | null;
};

export async function payloadFromProfile(profile: BirthRectificationProfile) {
  if (!profile.date || !profile.time) return null;
  const resolved = await resolveMissingBirthTimezoneOffset(profile, {
    preferredTime: profile.time,
  }) as BirthRectificationProfile;
  const province = chinaLocations.country.provinces.find((item) => item.code === profile.provinceCode);
  const city = province?.cities.find((item) => item.code === profile.cityCode);
  const district = city?.districts.find((item) => item.code === profile.districtCode);
  const location = district ?? city;
  const lat = finiteBirthNumber(resolved.latitude) ?? location?.center[1] ?? null;
  const lon = finiteBirthNumber(resolved.longitude) ?? location?.center[0] ?? null;
  const tz = finiteBirthNumber(resolved.timezoneOffset) ?? (location ? chinaLocations.country.timezone : null);
  if (lat === null || lon === null || tz === null) return null;
  return {
    birth_time: `${profile.date} ${profile.time}`,
    uncertainty_minutes: 30,
    step_minutes: 2,
    lat,
    lon,
    tz,
  };
}
