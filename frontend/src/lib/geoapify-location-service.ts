import type {
  BirthLocationSearchQuery,
  BirthLocationSearchResult,
  NormalizedBirthLocation,
} from "./location-contract";
import { chinaLocations } from "../data/china-locations";

type FetchLike = typeof fetch;
type JsonRecord = Record<string, unknown>;

function record(value: unknown): JsonRecord {
  return value && typeof value === "object" ? value as JsonRecord : {};
}

function text(value: unknown) {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function findChinaMatches(query: string, limit: number) {
  const needle = query.replace(/\s+/g, "").toLowerCase();
  const matches: Array<{
    code: string;
    type: "province" | "city" | "district";
    label: string;
    provinceCode: string;
    provinceName: string;
    cityName: string | null;
    districtName: string | null;
    latitude: number;
    longitude: number;
  }> = [];
  for (const province of chinaLocations.country.provinces) {
    if (province.name.toLowerCase().includes(needle)) matches.push({
      code: province.code,
      type: "province",
      label: `中国 · ${province.name}`,
      provinceCode: province.code,
      provinceName: province.name,
      cityName: null,
      districtName: null,
      latitude: province.center[1],
      longitude: province.center[0],
    });
    for (const city of province.cities) {
      if (city.name !== province.name && city.name.toLowerCase().includes(needle)) matches.push({
        code: city.code,
        type: "city",
        label: `中国 · ${province.name} · ${city.name}`,
        provinceCode: province.code,
        provinceName: province.name,
        cityName: city.name,
        districtName: null,
        latitude: city.center[1],
        longitude: city.center[0],
      });
      for (const district of city.districts) {
        if (!district.name.toLowerCase().includes(needle)) continue;
        matches.push({
          code: district.code,
          type: "district",
          label: `中国 · ${province.name} · ${city.name} · ${district.name}`,
          provinceCode: province.code,
          provinceName: province.name,
          cityName: city.name,
          districtName: district.name,
          latitude: district.center[1],
          longitude: district.center[0],
        });
      }
    }
  }
  return matches.slice(0, limit);
}

async function resolveTimezone(
  fetchImpl: FetchLike,
  apiBase: string,
  latitude: number,
  longitude: number,
  query: BirthLocationSearchQuery,
) {
  const response = await fetchImpl(`${apiBase}/api/location/timezone`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      latitude,
      longitude,
      ...(query.birthDate ? { birthDate: query.birthDate } : {}),
      ...(query.birthTime ? { birthTime: query.birthTime } : {}),
    }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("timezone_service_unavailable");
  const payload = record(await response.json());
  if (payload.available !== true || !text(payload.timezoneId)) {
    throw new Error("timezone_service_unavailable");
  }
  return payload;
}

export async function searchGlobalBirthLocations(
  query: BirthLocationSearchQuery,
  options: {
    apiKey?: string;
    apiBase?: string;
    fetchImpl?: FetchLike;
  } = {},
): Promise<BirthLocationSearchResult> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const apiBase = options.apiBase ?? process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200";
  const chinaMatches = findChinaMatches(query.q, query.limit);
  if (chinaMatches.length > 0) {
    try {
      const locations = await Promise.all(chinaMatches.map(async (match): Promise<NormalizedBirthLocation> => {
        const timezone = await resolveTimezone(fetchImpl, apiBase, match.latitude, match.longitude, query);
        return {
          provider: "china_locations",
          providerPlaceId: match.code,
          placeType: match.type,
          label: match.label,
          countryCode: "CN",
          countryName: "中国",
          regionCode: match.provinceCode,
          regionName: match.provinceName,
          localityName: match.cityName,
          districtName: match.districtName,
          latitude: match.latitude,
          longitude: match.longitude,
          timezoneId: String(timezone.timezoneId),
          timezoneOffset: typeof timezone.timezoneOffset === "number" ? timezone.timezoneOffset : null,
          timezoneSource: "iana_historical",
          localTimeStatus: ["resolved", "not_provided", "ambiguous", "nonexistent"].includes(String(timezone.localTimeStatus))
            ? timezone.localTimeStatus as NormalizedBirthLocation["localTimeStatus"]
            : "not_provided",
        };
      }));
      return { status: "ok", locations };
    } catch {
      return { status: "unavailable", reason: "timezone_service_unavailable" };
    }
  }

  const apiKey = options.apiKey?.trim() || process.env.GEOAPIFY_API_KEY?.trim();
  if (!apiKey) return { status: "unavailable", reason: "geoapify_not_configured" };
  const params = new URLSearchParams({
    text: query.q,
    apiKey,
    limit: String(query.limit),
    lang: query.locale.split("-")[0].toLowerCase(),
    format: "geojson",
  });

  let response: Response;
  try {
    response = await fetchImpl(`https://api.geoapify.com/v1/geocode/autocomplete?${params}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch {
    return { status: "unavailable", reason: "provider_unavailable" };
  }
  if (!response.ok) return { status: "unavailable", reason: "provider_unavailable" };
  const payload = record(await response.json());
  const features = Array.isArray(payload.features) ? payload.features : [];
  const normalized: NormalizedBirthLocation[] = [];

  for (const rawFeature of features) {
    const feature = record(rawFeature);
    const properties = record(feature.properties);
    const geometry = record(feature.geometry);
    const coordinates = Array.isArray(geometry.coordinates) ? geometry.coordinates.map(Number) : [];
    const longitude = coordinates[0] ?? Number(properties.lon);
    const latitude = coordinates[1] ?? Number(properties.lat);
    const providerPlaceId = text(properties.place_id);
    const label = text(properties.formatted) ?? text(properties.address_line1) ?? text(properties.name);
    const placeType = text(properties.result_type) ?? "locality";
    if (!providerPlaceId || !label || !Number.isFinite(latitude) || !Number.isFinite(longitude)) continue;
    try {
      const timezone = await resolveTimezone(fetchImpl, apiBase, latitude, longitude, query);
      normalized.push({
        provider: "geoapify",
        providerPlaceId,
        placeType,
        label,
        countryCode: text(properties.country_code)?.toUpperCase() ?? null,
        countryName: text(properties.country),
        regionCode: text(properties.state_code),
        regionName: text(properties.state),
        localityName: text(properties.city)
          ?? text(properties.town)
          ?? text(properties.village)
          ?? text(properties.municipality)
          ?? text(properties.suburb)
          ?? text(properties.name),
        districtName: text(properties.county) ?? text(properties.district),
        latitude,
        longitude,
        timezoneId: String(timezone.timezoneId),
        timezoneOffset: typeof timezone.timezoneOffset === "number" ? timezone.timezoneOffset : null,
        timezoneSource: "iana_historical",
        localTimeStatus: ["resolved", "not_provided", "ambiguous", "nonexistent"].includes(String(timezone.localTimeStatus))
          ? timezone.localTimeStatus as NormalizedBirthLocation["localTimeStatus"]
          : "not_provided",
      });
    } catch {
      return { status: "unavailable", reason: "timezone_service_unavailable" };
    }
  }
  return { status: "ok", locations: normalized };
}
