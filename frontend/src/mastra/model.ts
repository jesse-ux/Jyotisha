import type { MastraModelConfig } from "@mastra/core/llm";
import { z } from "zod";

type Environment = Readonly<Record<string, string | undefined>>;
type LanguageModelMode = "openai" | "compatible";

export type PublicLanguageModel = {
  readonly id: string;
  readonly label: string;
  readonly description: string;
  readonly creditCost: 1;
  readonly isDefault: boolean;
};

export type ResolvedLanguageModel = PublicLanguageModel & {
  readonly mode: LanguageModelMode;
  readonly model: MastraModelConfig;
};

export type LanguageModelCatalog = {
  readonly models: readonly ResolvedLanguageModel[];
  readonly publicModels: readonly PublicLanguageModel[];
  readonly defaultModelId: string | null;
  readonly issues: readonly string[];
};

const modelIdSchema = z.string().trim().min(1).max(64).regex(/^[a-z0-9][a-z0-9._-]*$/);
const apiKeyEnvironmentNameSchema = z.string().regex(/^[A-Z][A-Z0-9_]*$/);
const sharedCatalogFields = {
  id: modelIdSchema,
  label: z.string().trim().min(1).max(60),
  description: z.string().trim().max(100).default(""),
  apiKeyEnv: apiKeyEnvironmentNameSchema,
  model: z.string().trim().min(1).max(120),
  creditCost: z.literal(1),
};
const catalogEntrySchema = z.discriminatedUnion("provider", [
  z.object({
    ...sharedCatalogFields,
    provider: z.literal("openai"),
  }).strict(),
  z.object({
    ...sharedCatalogFields,
    provider: z.literal("openai-compatible"),
    baseURL: z.string().url().refine((value) => value.startsWith("https://")),
  }).strict(),
]);

type CatalogEntry = z.infer<typeof catalogEntrySchema>;

function environmentValue(environment: Environment, name: string) {
  return environment[name]?.trim() ?? "";
}

function publicModel(model: ResolvedLanguageModel): PublicLanguageModel {
  return {
    id: model.id,
    label: model.label,
    description: model.description,
    creditCost: model.creditCost,
    isDefault: model.isDefault,
  };
}

function resolveCatalogEntry(
  entry: CatalogEntry,
  apiKey: string,
  isDefault: boolean,
): ResolvedLanguageModel {
  const shared = {
    id: entry.id,
    label: entry.label,
    description: entry.description,
    creditCost: entry.creditCost,
    isDefault,
  } as const;

  switch (entry.provider) {
    case "openai":
      return {
        ...shared,
        mode: "openai",
        model: entry.model,
      };
    case "openai-compatible":
      return {
        ...shared,
        mode: "compatible",
        model: {
          providerId: entry.id,
          modelId: entry.model,
          url: entry.baseURL,
          apiKey,
        },
      };
  }
}

function resolveExplicitCatalog(environment: Environment, rawCatalog: string): LanguageModelCatalog {
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawCatalog);
  } catch {
    return { models: [], publicModels: [], defaultModelId: null, issues: ["catalog_json_invalid"] };
  }

  if (!Array.isArray(parsed)) {
    return { models: [], publicModels: [], defaultModelId: null, issues: ["catalog_not_array"] };
  }

  const defaultModelId = environmentValue(environment, "LLM_DEFAULT_MODEL_ID");
  const issues: string[] = [];
  const seenIds = new Set<string>();
  const models: ResolvedLanguageModel[] = [];

  parsed.forEach((value, index) => {
    const parsedEntry = catalogEntrySchema.safeParse(value);
    if (!parsedEntry.success) {
      issues.push(`catalog_entry_invalid:${index}`);
      return;
    }
    if (seenIds.has(parsedEntry.data.id)) {
      issues.push(`catalog_entry_duplicate:${index}`);
      return;
    }
    seenIds.add(parsedEntry.data.id);

    const apiKey = environmentValue(environment, parsedEntry.data.apiKeyEnv);
    if (!apiKey) {
      issues.push(`catalog_entry_secret_missing:${index}`);
      return;
    }
    models.push(resolveCatalogEntry(parsedEntry.data, apiKey, parsedEntry.data.id === defaultModelId));
  });

  const resolvedDefault = models.some((model) => model.id === defaultModelId)
    ? defaultModelId
    : null;
  if (!resolvedDefault) issues.push("default_model_unavailable");

  return {
    models,
    publicModels: models.map(publicModel),
    defaultModelId: resolvedDefault,
    issues,
  };
}

function resolveLegacyCatalog(environment: Environment): LanguageModelCatalog {
  const baseURL = environmentValue(environment, "LLM_BASE_URL");
  const apiKey = environmentValue(environment, "LLM_API_KEY");
  const modelId = environmentValue(environment, "LLM_MODEL");
  const hasCompatibleSetting = Boolean(baseURL || apiKey || modelId);

  if (hasCompatibleSetting) {
    if (!baseURL || !apiKey || !modelId || !baseURL.startsWith("https://")) {
      return {
        models: [],
        publicModels: [],
        defaultModelId: null,
        issues: ["legacy_compatible_incomplete"],
      };
    }
    const model: ResolvedLanguageModel = {
      id: "legacy-compatible",
      label: modelId,
      description: "当前默认模型",
      creditCost: 1,
      isDefault: true,
      mode: "compatible",
      model: {
        providerId: environmentValue(environment, "LLM_PROVIDER_ID") || "third-party",
        modelId,
        url: baseURL,
        apiKey,
      },
    };
    return {
      models: [model],
      publicModels: [publicModel(model)],
      defaultModelId: model.id,
      issues: [],
    };
  }

  const openAIKey = environmentValue(environment, "OPENAI_API_KEY");
  if (!openAIKey) {
    return { models: [], publicModels: [], defaultModelId: null, issues: ["model_not_configured"] };
  }
  const modelIdValue = environmentValue(environment, "MASTRA_MODEL") || "openai/gpt-5-mini";
  const model: ResolvedLanguageModel = {
    id: "legacy-openai",
    label: modelIdValue.replace(/^openai\//, ""),
    description: "当前默认模型",
    creditCost: 1,
    isDefault: true,
    mode: "openai",
    model: modelIdValue,
  };
  return {
    models: [model],
    publicModels: [publicModel(model)],
    defaultModelId: model.id,
    issues: [],
  };
}

export function resolveLanguageModelCatalog(environment: Environment): LanguageModelCatalog {
  const rawCatalog = environmentValue(environment, "LLM_MODELS_JSON");
  return rawCatalog
    ? resolveExplicitCatalog(environment, rawCatalog)
    : resolveLegacyCatalog(environment);
}

export const languageModelCatalog = resolveLanguageModelCatalog(process.env);

export function resolveLanguageModelFromCatalog(catalog: LanguageModelCatalog, modelId: string) {
  return catalog.models.find((model) => model.id === modelId) ?? null;
}

export function resolveLanguageModel(modelId: string) {
  return resolveLanguageModelFromCatalog(languageModelCatalog, modelId);
}

export function defaultLanguageModel() {
  const defaultModelId = languageModelCatalog.defaultModelId;
  return defaultModelId ? resolveLanguageModel(defaultModelId) : null;
}

export function publicLanguageModelCatalog() {
  return {
    models: languageModelCatalog.publicModels,
    defaultModelId: languageModelCatalog.defaultModelId,
  };
}

const configuredDefaultModel = defaultLanguageModel();

export const languageModelSettings = {
  mode: configuredDefaultModel?.mode ?? "openai",
  model: configuredDefaultModel?.model ?? "openai/gpt-5-mini",
  configured: Boolean(configuredDefaultModel),
  missing: languageModelCatalog.issues,
} as const;

export function languageModelConfigurationMessage() {
  return configuredDefaultModel ? null : "未配置可用的语言模型";
}
