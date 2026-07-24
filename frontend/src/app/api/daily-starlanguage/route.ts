import { NextResponse } from "next/server";
import {
  dailyProfilePayload,
  type GlobalBirthProfile as Profile,
} from "@/lib/global-birth-payloads";

const jyotishApiBase = process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200";

const cards = [
  { trend: "先收束，再推进。适合把一个悬而未决的问题拆小。", action: "选一件最重要的事，给它留出 45 分钟不被打断的时间。", caution: "避免在情绪最满时做承诺。" },
  { trend: "适合整理关系与边界。越清楚，越不容易被外界节奏带走。", action: "把今天要回复的人和要推迟的事分开列出来。", caution: "不要把暂时的沉默误读成最终答案。" },
  { trend: "执行力比灵感更重要。小步完成会比大计划更有力量。", action: "先完成一个可交付版本，再考虑优化。", caution: "别让完美感拖慢开始。" },
  { trend: "适合观察资源流向：时间、注意力、金钱都算。", action: "检查一个正在消耗你的习惯，并给它设上限。", caution: "不要为了短期安心做长期成本高的选择。" },
];

function pickCard(profile: Profile, today: string) {
  const seed = `${today}-${profile.date ?? ""}-${profile.time ?? ""}-${profile.provinceCode ?? ""}-${profile.cityCode ?? ""}`;
  const index = Array.from(seed).reduce((sum, char) => sum + char.charCodeAt(0), 0) % cards.length;
  return cards[index];
}

function chartPoints(chart: Record<string, unknown>) {
  const modules = chart.modules && typeof chart.modules === "object" ? chart.modules as Record<string, unknown> : {};
  const chartModule = modules.chart && typeof modules.chart === "object" ? modules.chart as Record<string, unknown> : chart;
  const planets = chartModule.planets && typeof chartModule.planets === "object" ? chartModule.planets : undefined;
  const ascendant = chartModule.ascendant && typeof chartModule.ascendant === "object" ? chartModule.ascendant : undefined;
  return planets && ascendant ? { planets, ascendant } : null;
}

async function fetchJson(path: string, body: Record<string, unknown>) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 2500);
  try {
    const response = await fetch(`${jyotishApiBase}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`jyotish_api_${response.status}`);
    return await response.json() as Record<string, unknown>;
  } finally {
    clearTimeout(timeout);
  }
}

async function transitBackedCard(profile: Profile, today: string) {
  const payload = await dailyProfilePayload(profile, today);
  if (!payload) return null;
  const chart = await fetchJson("/api/chart", payload);
  const points = chartPoints(chart);
  if (!points) return null;
  const tomorrow = new Date(`${today}T00:00:00.000Z`);
  tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
  const transit = await fetchJson("/api/transit", {
    natal_planets: points.planets,
    ascendant: points.ascendant,
    start: today,
    end: tomorrow.toISOString().slice(0, 10),
    planets_to_check: ["Saturn", "Jupiter", "Rahu", "Ketu"],
  });
  const summary = transit.summary && typeof transit.summary === "object" ? transit.summary as Record<string, unknown> : {};
  const total = Number(summary.total_triggers ?? 0);
  return {
    trend: total > 0 ? `今日有 ${total} 个可观察过境触发点，适合把它当作时间窗口观察。` : "今日未发现强精确过境触发，适合按本命节奏稳步推进。",
    action: "把今日计划压缩到一件主事，并记录实际发生的触发点。",
    caution: "过境触发不能单独定事件，需与 Dasha、分盘和本命承诺交叉确认。",
  };
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null) as { profile?: Profile; today?: string } | null;
  const profile = body?.profile ?? {};
  const today = body?.today || new Date().toISOString().slice(0, 10);
  const transitCard = await transitBackedCard(profile, today).catch(() => null);
  return NextResponse.json({
    status: "ok",
    card: transitCard ?? pickCard(profile, today),
    source: transitCard ? "jyotish_api_transit_lite" : "calculation_lite",
    claim_status: "exploratory_unvalidated",
    boundary: "not_deterministic_prediction",
  });
}
