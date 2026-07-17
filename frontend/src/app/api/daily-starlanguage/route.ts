import { NextResponse } from "next/server";

type Profile = {
  name?: string;
  date?: string;
  time?: string;
  provinceCode?: string;
  cityCode?: string;
};

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

export async function POST(request: Request) {
  const body = await request.json().catch(() => null) as { profile?: Profile; today?: string } | null;
  const profile = body?.profile ?? {};
  const today = body?.today || new Date().toISOString().slice(0, 10);
  return NextResponse.json({
    status: "ok",
    card: pickCard(profile, today),
    source: "calculation_lite",
    claim_status: "exploratory_unvalidated",
    boundary: "not_deterministic_prediction",
  });
}
