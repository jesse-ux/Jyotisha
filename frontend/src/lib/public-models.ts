import { z } from "zod";

const publicLanguageModelSchema = z.object({
  id: z.string().trim().min(1).max(64).regex(/^[a-z0-9][a-z0-9._-]*$/),
  label: z.string().trim().min(1).max(60),
  description: z.string().trim().max(100),
  creditCost: z.literal(1),
  isDefault: z.boolean(),
}).strict();

const publicLanguageModelCatalogSchema = z.object({
  models: z.array(publicLanguageModelSchema).min(1),
  defaultModelId: z.string().trim().min(1).max(64),
}).strict().superRefine((catalog, context) => {
  const ids = new Set(catalog.models.map((model) => model.id));
  if (ids.size !== catalog.models.length) {
    context.addIssue({ code: z.ZodIssueCode.custom, message: "model_ids_not_unique" });
  }
  const declaredDefault = catalog.models.filter((model) => model.isDefault);
  if (declaredDefault.length !== 1 || declaredDefault[0]?.id !== catalog.defaultModelId) {
    context.addIssue({ code: z.ZodIssueCode.custom, message: "default_model_mismatch" });
  }
});

export type PublicLanguageModel = {
  readonly id: string;
  readonly label: string;
  readonly description: string;
  readonly creditCost: 1;
  readonly isDefault: boolean;
};

export type PublicLanguageModelCatalog = {
  readonly models: readonly PublicLanguageModel[];
  readonly defaultModelId: string;
};

export function parsePublicModelCatalog(value: unknown): PublicLanguageModelCatalog {
  return publicLanguageModelCatalogSchema.parse(value);
}

export function resolveSessionModelId(
  savedModelId: unknown,
  catalog: PublicLanguageModelCatalog,
) {
  const modelId = typeof savedModelId === "string" ? savedModelId : "";
  const remainsAvailable = catalog.models.some((model) => model.id === modelId);
  return remainsAvailable
    ? { modelId, fellBack: false } as const
    : { modelId: catalog.defaultModelId, fellBack: true } as const;
}
