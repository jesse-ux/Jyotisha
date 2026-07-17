import assert from "node:assert/strict";
import test from "node:test";
import { parsePublicModelCatalog } from "../src/lib/public-models.ts";

const publicPayload = {
  defaultModelId: "deepseek-pro",
  models: [
    {
      id: "deepseek-pro",
      label: "DeepSeek V4 Pro",
      description: "复杂分析",
      creditCost: 1,
      isDefault: true,
    },
    {
      id: "gpt-mini",
      label: "ChatGPT Mini",
      description: "均衡响应",
      creditCost: 1,
      isDefault: false,
    },
  ],
} as const;

test("parses a sanitized public model catalog", () => {
  // Given
  const payload: unknown = publicPayload;

  // When
  const catalog = parsePublicModelCatalog(payload);

  // Then
  assert.equal(catalog.defaultModelId, "deepseek-pro");
  assert.equal(catalog.models.length, 2);
  assert.equal(catalog.models[0]?.label, "DeepSeek V4 Pro");
});

test("rejects provider routing fields in a public model payload", () => {
  // Given
  const payload = {
    ...publicPayload,
    models: [{
      ...publicPayload.models[0],
      baseURL: "https://api.deepseek.com",
      apiKeyEnv: "DEEPSEEK_API_KEY",
    }],
  };

  // When
  const parse = () => parsePublicModelCatalog(payload);

  // Then
  assert.throws(parse);
});

test("rejects a default model that is absent from the public list", () => {
  // Given
  const payload = {
    ...publicPayload,
    defaultModelId: "removed-model",
  };

  // When
  const parse = () => parsePublicModelCatalog(payload);

  // Then
  assert.throws(parse);
});
