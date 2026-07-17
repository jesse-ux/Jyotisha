import { NextResponse } from "next/server";
import { z } from "zod";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { getOnboardingAgent } from "@/mastra";
import { defaultLanguageModel } from "@/mastra/model";

export const runtime = "nodejs";
export const maxDuration = 30;

const ONBOARDING_VERSION = "ayanam-onboarding-v3";
const ONBOARDING_PENDING_VERSION = `${ONBOARDING_VERSION}:pending`;
const ONBOARDING_CLAIM_TTL_MS = 2 * 60 * 1000;

const onboardingSchema = z.object({
  greeting: z.string().trim().min(8).max(180),
  suggestions: z.tuple([
    z.object({ theme: z.literal("career"), text: z.string().trim().min(4).max(80) }),
    z.object({ theme: z.literal("marriage"), text: z.string().trim().min(4).max(80) }),
    z.object({ theme: z.literal("timing"), text: z.string().trim().min(4).max(80) }),
  ]),
});

type OnboardingPayload = z.infer<typeof onboardingSchema>;

const fallbackPayload: OnboardingPayload = {
  greeting: "我们从你此刻最关心的事情开始。可以选择下面的方向，也可以直接说出你的问题。",
  suggestions: [
    { theme: "career", text: "我的事业优势更适合怎样发挥？" },
    { theme: "marriage", text: "我在关系里容易重复什么模式？" },
    { theme: "timing", text: "未来一年有哪些阶段值得提前准备？" },
  ],
};

function parseJsonObject(text: string) {
  const normalized = text.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
  const start = normalized.indexOf("{");
  const end = normalized.lastIndexOf("}");
  if (start < 0 || end <= start) throw new Error("onboarding_json_missing");
  return JSON.parse(normalized.slice(start, end + 1));
}

function hasCompleteBirthProfile(profile: Record<string, unknown>) {
  return Boolean(
    profile.name
    && profile.birth_date
    && (profile.active_birth_time || profile.birth_time)
    && (profile.birth_time_status === "confirmed" || (!profile.birth_time_status && profile.birth_time))
    && profile.country_code
    && profile.province_code
    && profile.city_code,
  );
}

export async function POST() {
  let supabase: Awaited<ReturnType<typeof createServerSupabaseClient>>;
  let admin: ReturnType<typeof createAdminSupabaseClient>;
  try {
    supabase = await createServerSupabaseClient();
    admin = createAdminSupabaseClient();
  } catch {
    return NextResponse.json(
      { error: "服务尚未配置", message: "请先配置 Supabase 环境变量。" },
      { status: 503 },
    );
  }

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: "请先登录", message: "登录后才能准备初始问题。" },
      { status: 401 },
    );
  }

  const { data: profile, error: profileError } = await admin
    .from("profiles")
    .select("name,birth_date,birth_time,active_birth_time,birth_time_status,country_code,province_code,city_code,onboarding_payload,onboarding_version,onboarding_generated_at")
    .eq("id", user.id)
    .maybeSingle();

  if (profileError || !profile) {
    return NextResponse.json(
      { error: "无法读取用户档案", message: profileError?.message || "请重新登录后再试。" },
      { status: 503 },
    );
  }

  if (!hasCompleteBirthProfile(profile)) {
    return NextResponse.json(
      { error: "出生资料尚未完成", message: "请先填写称呼、出生日期、时间和地点。" },
      { status: 409 },
    );
  }

  if (profile.onboarding_version === ONBOARDING_VERSION) {
    const cached = onboardingSchema.safeParse(profile.onboarding_payload);
    if (cached.success) {
      return NextResponse.json({ ...cached.data, source: "cache" });
    }
  }

  const generatedAt = typeof profile.onboarding_generated_at === "string"
    ? Date.parse(profile.onboarding_generated_at)
    : 0;
  const activeClaim = profile.onboarding_version === ONBOARDING_PENDING_VERSION
    && Number.isFinite(generatedAt)
    && Date.now() - generatedAt < ONBOARDING_CLAIM_TTL_MS;
  if (activeClaim) {
    return NextResponse.json({ ...fallbackPayload, source: "pending" });
  }

  const claimTime = new Date().toISOString();
  let claim = admin
    .from("profiles")
    .update({
      onboarding_version: ONBOARDING_PENDING_VERSION,
      onboarding_generated_at: claimTime,
    })
    .eq("id", user.id);
  claim = profile.onboarding_version === null
    ? claim.is("onboarding_version", null)
    : claim.eq("onboarding_version", profile.onboarding_version);
  const { data: claimedProfile, error: claimError } = await claim.select("id").maybeSingle();
  if (claimError) {
    return NextResponse.json(
      { error: "暂时无法准备初始问题", message: claimError.message },
      { status: 503 },
    );
  }
  if (!claimedProfile) {
    return NextResponse.json({ ...fallbackPayload, source: "pending" });
  }

  let payload = fallbackPayload;
  let source: "agent" | "fallback" = "fallback";

  const onboardingModel = defaultLanguageModel();
  if (onboardingModel) {
    try {
      const result = await getOnboardingAgent(onboardingModel).generate([
        {
          role: "user",
          content: [
            profile.name ? `用户称呼：${String(profile.name).slice(0, 80)}` : "用户未填写称呼。",
            "请生成首次欢迎语和三个入门问题。欢迎语直接邀请用户提问，不要提到出生资料、资料准备或系统处理过程。",
          ].join("\n"),
        },
      ]);
      const parsed = onboardingSchema.safeParse(parseJsonObject(result.text));
      if (parsed.success) {
        payload = parsed.data;
        source = "agent";
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "unknown error";
      console.warn("[onboarding] agent generation failed; using safe fallback", message);
    }
  }

  const { error: cacheError } = await admin
    .from("profiles")
    .update({
      onboarding_payload: payload,
      onboarding_version: ONBOARDING_VERSION,
      onboarding_generated_at: new Date().toISOString(),
    })
    .eq("id", user.id)
    .eq("onboarding_version", ONBOARDING_PENDING_VERSION);

  if (cacheError) {
    console.warn("[onboarding] unable to cache generated content", cacheError.message);
  }

  return NextResponse.json({ ...payload, source });
}
