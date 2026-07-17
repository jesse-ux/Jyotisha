import assert from "node:assert/strict";
import test from "node:test";
import { resolveLanguageModelCatalog } from "../src/mastra/model.ts";

const configuredModels = [
  {
    id: "deepseek-pro",
    label: "DeepSeek V4 Pro",
    description: "复杂分析",
    provider: "openai-compatible",
    baseURL: "https://api.deepseek.com",
    apiKeyEnv: "DEEPSEEK_API_KEY",
    model: "deepseek-v4-pro",
    creditCost: 1,
  },
  {
    id: "gpt-mini",
    label: "ChatGPT Mini",
    description: "均衡响应",
    provider: "openai",
    apiKeyEnv: "OPENAI_API_KEY",
    model: "openai/gpt-5-mini",
    creditCost: 1,
  },
] as const;

test("resolves configured models while returning sanitized public metadata", () => {
  // Given
  const environment = {
    LLM_DEFAULT_MODEL_ID: "deepseek-pro",
    LLM_MODELS_JSON: JSON.stringify(configuredModels),
    DEEPSEEK_API_KEY: "deepseek-secret",
    OPENAI_API_KEY: "openai-secret",
  };

  // When
  const catalog = resolveLanguageModelCatalog(environment);

  // Then
  assert.equal(catalog.defaultModelId, "deepseek-pro");
  assert.deepEqual(catalog.publicModels[0], {
    id: "deepseek-pro",
    label: "DeepSeek V4 Pro",
    description: "复杂分析",
    creditCost: 1,
    isDefault: true,
  });
  assert.equal(JSON.stringify(catalog.publicModels).includes("secret"), false);
  assert.equal(JSON.stringify(catalog.publicModels).includes("baseURL"), false);
  assert.equal(catalog.models[1]?.model, "openai/gpt-5-mini");
});

test("excludes an invalid catalog entry without leaking its secret", () => {
  // Given
  const environment = {
    LLM_DEFAULT_MODEL_ID: "gpt-mini",
    LLM_MODELS_JSON: JSON.stringify([
      configuredModels[1],
      {
        ...configuredModels[0],
        id: "broken model",
        baseURL: "http://api.deepseek.com",
      },
    ]),
    OPENAI_API_KEY: "openai-secret",
    DEEPSEEK_API_KEY: "must-not-appear",
  };

  // When
  const catalog = resolveLanguageModelCatalog(environment);

  // Then
  assert.deepEqual(catalog.models.map((model) => model.id), ["gpt-mini"]);
  assert.equal(catalog.issues.length, 1);
  assert.equal(JSON.stringify(catalog.issues).includes("must-not-appear"), false);
});

test("does not choose an undeclared default model", () => {
  // Given
  const environment = {
    LLM_DEFAULT_MODEL_ID: "removed-model",
    LLM_MODELS_JSON: JSON.stringify([configuredModels[1]]),
    OPENAI_API_KEY: "openai-secret",
  };

  // When
  const catalog = resolveLanguageModelCatalog(environment);

  // Then
  assert.equal(catalog.defaultModelId, null);
  assert.equal(catalog.issues.includes("default_model_unavailable"), true);
});

test("derives the shipped compatible-provider configuration when no catalog exists", () => {
  // Given
  const environment = {
    LLM_BASE_URL: "https://api.deepseek.com",
    LLM_API_KEY: "legacy-secret",
    LLM_MODEL: "deepseek-v4-pro",
    LLM_PROVIDER_ID: "deepseek",
  };

  // When
  const catalog = resolveLanguageModelCatalog(environment);

  // Then
  assert.equal(catalog.defaultModelId, "legacy-compatible");
  assert.equal(catalog.models[0]?.id, "legacy-compatible");
  assert.equal(catalog.publicModels[0]?.label, "deepseek-v4-pro");
  assert.equal(JSON.stringify(catalog.publicModels).includes("legacy-secret"), false);
});

test("reports an incomplete legacy provider without inventing a model", () => {
  // Given
  const environment = {
    LLM_BASE_URL: "https://api.deepseek.com",
    LLM_MODEL: "deepseek-v4-pro",
  };

  // When
  const catalog = resolveLanguageModelCatalog(environment);

  // Then
  assert.equal(catalog.models.length, 0);
  assert.equal(catalog.defaultModelId, null);
  assert.equal(catalog.issues.includes("legacy_compatible_incomplete"), true);
});
