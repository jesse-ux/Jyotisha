import { Agent } from "@mastra/core/agent";
import { z } from "zod";
import { defaultLanguageModel, resolveLanguageModel } from "@/mastra/model";
import {
  eventKindSchema,
  eventSubjectSchema,
  evidenceDomainSchema,
  relatedPersonSchema,
} from "../rectification-v4/contracts.ts";
import {
  validatedModelAssistedEvidence,
  type ExtractedLifeEventEvidence,
  type ModelAssistedEventExtraction,
} from "../conversational-rectification/evidence-extractor.ts";

export const modelAssistedEventExtractionSchema = z.object({
  sourceSpan: z.string().trim().min(1).max(4_000),
  summary: z.string().trim().min(1).max(1_000),
  domain: evidenceDomainSchema,
  eventKind: eventKindSchema,
  subject: eventSubjectSchema,
  relatedPerson: relatedPersonSchema.nullable(),
  dateText: z.string().trim().min(1).max(80).nullable(),
}).strict();

export type EventExtractorGenerator = (prompt: string) => Promise<Readonly<{ object: unknown }>>;

export async function extractEventWithModel(input: Readonly<{
  rawText: string;
  sourceTurnId: string;
  asOfDate: string;
  modelId?: string | null;
  timeoutMs?: number;
  generateExtraction?: EventExtractorGenerator;
}>): Promise<ExtractedLifeEventEvidence | null> {
  const model = (input.modelId ? resolveLanguageModel(input.modelId) : null) ?? defaultLanguageModel();
  if (!model && !input.generateExtraction) return null;
  const agent = model ? new Agent({
    id: `rectification-event-extractor-${model.id}`,
    name: "Restricted Rectification Event Extractor",
    model: model.model,
    instructions: "Extract at most one explicitly stated dated life event. sourceSpan and dateText must be exact continuous substrings of the user text. Never infer or invent a date, normalized range, candidate time, score, id, or profile value. Return strict JSON only.",
  }) : null;
  const generate = input.generateExtraction ?? (async (prompt: string) => {
    if (!agent) throw new Error("event_extractor_model_unavailable");
    return agent.generate(prompt, {
      abortSignal: AbortSignal.timeout(input.timeoutMs ?? 10_000),
      structuredOutput: { schema: modelAssistedEventExtractionSchema, jsonPromptInjection: "inline" },
    });
  });
  try {
    const result = await generate(JSON.stringify({
      task: "Extract one event that deterministic parsing could not classify. Use only literal text from userText.",
      userText: input.rawText,
      asOfDate: input.asOfDate,
      allowedOutput: ["sourceSpan", "summary", "domain", "eventKind", "subject", "relatedPerson", "dateText"],
    }));
    const extraction = modelAssistedEventExtractionSchema.parse(result.object) as ModelAssistedEventExtraction;
    return validatedModelAssistedEvidence({
      rawText: input.rawText,
      sourceTurnId: input.sourceTurnId,
      asOfDate: input.asOfDate,
      extraction,
    });
  } catch {
    return null;
  }
}
