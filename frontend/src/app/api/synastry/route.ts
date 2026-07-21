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

type RelationshipType = "romance" | "business" | "family" | "general";

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

function moonSummary(chart: Record<string, unknown>) {
  const planets = chart.planets && typeof chart.planets === "object" ? chart.planets as Record<string, unknown> : {};
  const moon = planets.Moon && typeof planets.Moon === "object" ? planets.Moon as Record<string, unknown> : {};
  return {
    sign: moon.sign,
    nakshatra: moon.nakshatra,
    pada: moon.nakshatra_pada,
    lord: moon.nakshatra_lord,
    longitude: moonLongitude(chart),
  };
}

function d9Summary(varga: Record<string, unknown>) {
  const result = varga.result && typeof varga.result === "object" ? varga.result as Record<string, unknown> : {};
  const d9 = result.D9_Navamsa && typeof result.D9_Navamsa === "object" ? result.D9_Navamsa as Record<string, unknown> : {};
  const ascendant = d9.ascendant && typeof d9.ascendant === "object" ? d9.ascendant as Record<string, unknown> : {};
  const planets = d9.planets && typeof d9.planets === "object" ? d9.planets as Record<string, unknown> : {};
  return {
    ascendant,
    moon: planets.Moon,
    venus: planets.Venus,
    mars: planets.Mars,
    source: varga.source,
  };
}

function planetSign(point: unknown) {
  return point && typeof point === "object" && "sign" in point
    ? String((point as Record<string, unknown>).sign || "unknown")
    : "unknown";
}

function relationshipReport(synastry: Record<string, unknown>, selfD9: Record<string, unknown>, partnerD9: Record<string, unknown>) {
  const total = Number(synastry.total_score ?? 0);
  const max = Number(synastry.max_score ?? 36);
  const ratio = max > 0 ? total / max : 0;
  const band = ratio >= 0.72 ? "supportive" : ratio >= 0.5 ? "mixed" : "challenging";
  const self = d9Summary(selfD9);
  const partner = d9Summary(partnerD9);
  return {
    status: "evidence_summary",
    scoreBand: band,
    headline: band === "supportive"
      ? "基础匹配度偏支持，但仍需结合现实互动与长期运势。"
      : band === "mixed"
        ? "基础匹配度中等，适合重点观察沟通节奏、价值观与关系承诺。"
        : "基础匹配度偏谨慎，需要先处理冲突模式与现实条件。",
    strengths: [
      `Ashtakoot ${total}/${max}`,
      `本人 D9 Moon：${planetSign(self.moon)}`,
      `对方 D9 Moon：${planetSign(partner.moon)}`,
    ],
    risks: [
      "这不是完整婚恋结论；尚未纳入双方 Dasha、UL/DK 与长期时机。",
      `D9 Venus/Mars 需要继续解释：本人 ${planetSign(self.venus)}/${planetSign(self.mars)}，对方 ${planetSign(partner.venus)}/${planetSign(partner.mars)}。`,
    ],
    nextEvidence: ["双方 Dasha", "UL/DK", "D9 7宫/7主", "现实关系时间线"],
  };
}

function vargaPlanetSign(varga: Record<string, unknown>, division: string, planet: string) {
  const result = varga.result && typeof varga.result === "object" ? varga.result as Record<string, unknown> : {};
  const chart = result[division] && typeof result[division] === "object" ? result[division] as Record<string, unknown> : {};
  const planets = chart.planets && typeof chart.planets === "object" ? chart.planets as Record<string, unknown> : {};
  return planetSign(planet === "Ascendant" ? chart.ascendant : planets[planet]);
}

function businessReport(selfVargas: Record<string, unknown>, partnerVargas: Record<string, unknown>) {
  return {
    status: "partial_evidence",
    scoreBand: "not_scored",
    headline: "已完成基础合作结构筛查；这不是合作成败、收益或契约保证。",
    strengths: [
      `D10 事业轴：本人 ${vargaPlanetSign(selfVargas, "D10_Dasamsa", "Ascendant")} / 对方 ${vargaPlanetSign(partnerVargas, "D10_Dasamsa", "Ascendant")}`,
      `D2 财富轴：本人 Moon ${vargaPlanetSign(selfVargas, "D2_Hora", "Moon")} / 对方 Moon ${vargaPlanetSign(partnerVargas, "D2_Hora", "Moon")}`,
      `D11 收益轴：本人 Sun ${vargaPlanetSign(selfVargas, "D11_Rudramsa", "Sun")} / 对方 Sun ${vargaPlanetSign(partnerVargas, "D11_Rudramsa", "Sun")}`,
    ],
    risks: [
      "尚未完成 A10、功能吉凶、双方 Vimshottari + Narayana、Shadbala/AV 与外部数值一致性，不得据此断言合作结果或精确时点。",
    ],
    nextEvidence: ["A10", "功能吉凶", "双方 Vimshottari + Narayana", "D10/D2/D11 原始度数与外部校验"],
  };
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
    const body = await request.json().catch(() => null) as { selfProfile?: Profile; partnerProfile?: Profile; relationshipType?: RelationshipType } | null;
    if (!body?.selfProfile || !body.partnerProfile) {
      return NextResponse.json({ error: "请提供双方星盘资料" }, { status: 400 });
    }
    const selfChart = await postPython("/api/chart", birthPayload(body.selfProfile));
    const partnerChart = await postPython("/api/chart", birthPayload(body.partnerProfile));
    const relationshipType = body.relationshipType === "business" || body.relationshipType === "family" || body.relationshipType === "general"
      ? body.relationshipType
      : "romance";
    if (relationshipType === "business") {
      const [selfVargas, partnerVargas] = await Promise.all([
        postPython("/api/varga_full", { ...birthPayload(body.selfProfile), planets: selfChart.planets, ascendant: selfChart.ascendant, divisions: ["D2", "D10", "D11"] }),
        postPython("/api/varga_full", { ...birthPayload(body.partnerProfile), planets: partnerChart.planets, ascendant: partnerChart.ascendant, divisions: ["D2", "D10", "D11"] }),
      ]);
      return NextResponse.json({
        status: "ok",
        relationshipType,
        claimStatus: "partial",
        method: "d2_d10_d11_business_screening_partial",
        evidenceLayers: ["d2_hora", "d10_dashamsa", "d11_ekadashamsa"],
        blockedLayers: ["A10", "functional_benefic_malefic", "vimshottari_narayana", "shadbala_ashtakavarga", "external_engine_parity"],
        relationshipReport: businessReport(selfVargas, partnerVargas),
      });
    }
    if (relationshipType !== "romance") {
      return NextResponse.json({
        status: "blocked",
        relationshipType,
        message: "该关系类型尚无可验证的专用合盘计算合同；已保留问题草稿。",
      });
    }
    const selfD9 = await postPython("/api/varga_full", {
      ...birthPayload(body.selfProfile),
      planets: selfChart.planets,
      ascendant: selfChart.ascendant,
      divisions: ["D9"],
    });
    const partnerD9 = await postPython("/api/varga_full", {
      ...birthPayload(body.partnerProfile),
      planets: partnerChart.planets,
      ascendant: partnerChart.ascendant,
      divisions: ["D9"],
    });
    const synastry = await postPython("/api/synastry", {
      male_moon: moonLongitude(selfChart),
      female_moon: moonLongitude(partnerChart),
    });
    return NextResponse.json({
      status: "ok",
      method: "ashtakoot_plus_moon_nakshatra_d9",
      evidenceLayers: ["ashtakoot", "moon_nakshatra", "d9_navamsa"],
      selfChart: { moon: moonSummary(selfChart), d9: d9Summary(selfD9) },
      partnerChart: { moon: moonSummary(partnerChart), d9: d9Summary(partnerD9) },
      synastry,
      relationshipReport: relationshipReport(synastry, selfD9, partnerD9),
    });
  } catch (error) {
    return NextResponse.json({
      status: "blocked",
      error: error instanceof Error ? error.message : "synastry_unavailable",
      message: "合盘计算暂时不可用；可先保留合盘问题草稿。",
    }, { status: 503 });
  }
}
