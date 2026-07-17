import { NextResponse } from "next/server";
import { chinaLocations } from "@/data/china-locations";

type Profile = {
  name?: string;
  date?: string;
  time?: string;
  countryCode?: "CN";
  provinceCode?: string;
  cityCode?: string;
  districtCode?: string;
};

const apiBase = process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200";
const china = chinaLocations.country;

function birthPayload(profile: Profile) {
  const [year, month, day] = String(profile.date || "").split("-").map(Number);
  const [hour, minute] = String(profile.time || "").split(":").map(Number);
  const province = china.provinces.find((item) => item.code === profile.provinceCode);
  const city = province?.cities.find((item) => item.code === profile.cityCode);
  const district = city?.districts.find((item) => item.code === profile.districtCode);
  const location = district ?? city;
  if (![year, month, day, hour, minute].every(Number.isFinite) || !location) {
    throw new Error("birth_profile_incomplete");
  }
  return {
    year, month, day, hour, minute,
    second: 0,
    lat: location.center[1],
    lon: location.center[0],
    tz: china.timezone,
  };
}

function moonLongitude(chart: Record<string, unknown>) {
  const planets = chart.planets && typeof chart.planets === "object" ? chart.planets as Record<string, unknown> : {};
  const moon = planets.Moon && typeof planets.Moon === "object" ? planets.Moon as Record<string, unknown> : {};
  const value = moon.lon ?? moon.longitude ?? moon.degree;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) throw new Error("moon_longitude_missing");
  return numeric;
}

async function postPython(path: string, body: unknown) {
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(45_000),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok || !data || typeof data !== "object") {
    throw new Error(`jyotish_api_${response.status}`);
  }
  return data as Record<string, unknown>;
}

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => null) as { selfProfile?: Profile; partnerProfile?: Profile } | null;
    if (!body?.selfProfile || !body.partnerProfile) {
      return NextResponse.json({ error: "请提供双方星盘资料" }, { status: 400 });
    }
    const selfChart = await postPython("/api/chart", birthPayload(body.selfProfile));
    const partnerChart = await postPython("/api/chart", birthPayload(body.partnerProfile));
    const synastry = await postPython("/api/synastry", {
      male_moon: moonLongitude(selfChart),
      female_moon: moonLongitude(partnerChart),
    });
    return NextResponse.json({
      status: "ok",
      method: "ashtakoot_from_computed_moon",
      selfChart: { moon: moonLongitude(selfChart) },
      partnerChart: { moon: moonLongitude(partnerChart) },
      synastry,
    });
  } catch (error) {
    return NextResponse.json({
      status: "blocked",
      error: error instanceof Error ? error.message : "synastry_unavailable",
      message: "合盘计算暂时不可用；可先保留合盘问题草稿。",
    }, { status: 503 });
  }
}
