import type { MastraModelConfig } from "@mastra/core/llm";

type LanguageModelMode = "openai" | "compatible";

type LanguageModelSettings = {
  mode: LanguageModelMode;
  model: MastraModelConfig;
  configured: boolean;
  missing: string[];
};

function environmentValue(name: string) {
  return process.env[name]?.trim() ?? "";
}

/**
 * Resolves either the default OpenAI model or a third-party endpoint that
 * implements the OpenAI Chat Completions API. A supplied LLM_* value switches
 * the app to compatible-provider mode, so the old OPENAI_* setup remains
 * backwards compatible.
 */
function resolveLanguageModelSettings(): LanguageModelSettings {
  const baseURL = environmentValue("LLM_BASE_URL");
  const apiKey = environmentValue("LLM_API_KEY");
  const modelId = environmentValue("LLM_MODEL");
  const hasCompatibleSetting = Boolean(baseURL || apiKey || modelId);

  if (hasCompatibleSetting) {
    const missing = [
      !baseURL && "LLM_BASE_URL",
      !apiKey && "LLM_API_KEY",
      !modelId && "LLM_MODEL",
    ].filter((value): value is string => Boolean(value));

    return {
      mode: "compatible",
      configured: missing.length === 0,
      missing,
      model: {
        // This is an internal label for Mastra. It does not need to match the
        // provider's company name; the URL determines the actual endpoint.
        providerId: environmentValue("LLM_PROVIDER_ID") || "third-party",
        modelId: modelId || "not-configured",
        url: baseURL || undefined,
        apiKey: apiKey || undefined,
      },
    };
  }

  const openAIKey = environmentValue("OPENAI_API_KEY");
  return {
    mode: "openai",
    configured: Boolean(openAIKey),
    missing: openAIKey ? [] : ["OPENAI_API_KEY"],
    model: environmentValue("MASTRA_MODEL") || "openai/gpt-5-mini",
  };
}

export const languageModelSettings = resolveLanguageModelSettings();

export function languageModelConfigurationMessage() {
  if (languageModelSettings.configured) return null;

  if (languageModelSettings.mode === "compatible") {
    return `第三方模型配置不完整：${languageModelSettings.missing.join("、")}`;
  }

  return "未配置 OPENAI_API_KEY";
}
