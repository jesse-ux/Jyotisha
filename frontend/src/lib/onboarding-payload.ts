import { z } from "zod";

const onboardingSchema = z.object({
  greeting: z.string().trim().min(8).max(180),
  suggestions: z.tuple([
    z.object({ theme: z.literal("career"), text: z.string().trim().min(4).max(80) }),
    z.object({ theme: z.literal("marriage"), text: z.string().trim().min(4).max(80) }),
    z.object({ theme: z.literal("timing"), text: z.string().trim().min(4).max(80) }),
  ]),
});

export type OnboardingPayload = z.infer<typeof onboardingSchema>;

export const fallbackOnboardingPayload: OnboardingPayload = {
  greeting: "我们从你此刻最关心的事情开始。可以选择下面的方向，也可以直接说出你的问题。",
  suggestions: [
    { theme: "career", text: "我的事业优势更适合怎样发挥？" },
    { theme: "marriage", text: "我在关系里容易重复什么模式？" },
    { theme: "timing", text: "未来一年有哪些阶段值得提前准备？" },
  ],
};

class OnboardingJsonError extends Error {
  readonly name = "OnboardingJsonError";
}

export function parseOnboardingPayload(value: unknown): OnboardingPayload | null {
  const parsed = onboardingSchema.safeParse(value);
  return parsed.success ? parsed.data : null;
}

export function parseOnboardingText(text: string): OnboardingPayload | null {
  const normalized = text.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
  const start = normalized.indexOf("{");
  const end = normalized.lastIndexOf("}");
  if (start < 0 || end <= start) throw new OnboardingJsonError("onboarding_json_missing");
  const parsed: unknown = JSON.parse(normalized.slice(start, end + 1));
  return parseOnboardingPayload(parsed);
}
