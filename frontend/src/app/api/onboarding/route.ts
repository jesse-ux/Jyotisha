import {
  createOnboardingPost,
  type OnboardingProfileRepository,
} from "@/lib/onboarding-post";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { getOnboardingAgent } from "@/mastra";
import { defaultLanguageModel, resolveLanguageModel } from "@/mastra/model";

export const runtime = "nodejs";
export const maxDuration = 30;

function createProfileRepository(
  admin: ReturnType<typeof createAdminSupabaseClient>,
): OnboardingProfileRepository {
  return {
    async loadProfile(userId) {
      return admin
        .from("profiles")
        .select("id,name,birth_date,birth_time,reported_birth_time,active_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,birth_time_status,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset,birth_place_label,birth_place_type,birth_place_provider,birth_place_provider_id,timezone_id,timezone_source,onboarding_payload,onboarding_version,onboarding_generated_at")
        .eq("id", userId)
        .maybeSingle();
    },
    async claimProfile(command) {
      let claim = admin
        .from("profiles")
        .update({
          onboarding_version: command.pendingVersion,
          onboarding_generated_at: command.claimedAt,
        })
        .eq("id", command.userId);
      claim = command.expectedVersion === null
        ? claim.is("onboarding_version", null)
        : claim.eq("onboarding_version", command.expectedVersion);
      claim = command.expectedGeneratedAt === null
        ? claim.is("onboarding_generated_at", null)
        : claim.eq("onboarding_generated_at", command.expectedGeneratedAt);
      return claim.select("id").maybeSingle();
    },
    async completeProfile(command) {
      return admin
        .from("profiles")
        .update({
          onboarding_payload: command.payload,
          onboarding_version: command.readyVersion,
          onboarding_generated_at: command.generatedAt,
        })
        .eq("id", command.userId)
        .eq("onboarding_version", command.expectedPendingVersion)
        .select("id")
        .maybeSingle();
    },
  };
}

export const POST = createOnboardingPost({
  openSession: async () => {
    const supabase = await createServerSupabaseClient();
    const admin = createAdminSupabaseClient();
    const { data: { user }, error } = await supabase.auth.getUser();
    return {
      userId: user?.id ?? null,
      authError: Boolean(error),
      repository: createProfileRepository(admin),
    };
  },
  generateText: async (name, signal) => {
    const preferredModelId = process.env.ONBOARDING_MODEL_ID?.trim() || "deepseek-v4-flash";
    const model = resolveLanguageModel(preferredModelId) ?? defaultLanguageModel();
    if (!model) return null;
    const result = await getOnboardingAgent(model).generate([
      {
        role: "user",
        content: [
          name ? `用户称呼：${name.slice(0, 80)}` : "用户未填写称呼。",
          "请生成首次欢迎语和三个入门问题。欢迎语直接邀请用户提问，不要提到出生资料、资料准备或系统处理过程。",
        ].join("\n"),
      },
    ], { abortSignal: signal });
    return result.text;
  },
  now: () => new Date(),
  warn: (message, detail) => console.warn(message, detail),
});
