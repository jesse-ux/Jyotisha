const promptExtractionPatterns = [
  /(?:ignore|disregard).{0,24}(?:previous|system|developer).{0,24}(?:instruction|prompt)/i,
  /(?:忽略|无视).{0,20}(?:之前|以上|系统|开发者).{0,20}(?:指令|提示词)/,
  /(?:system prompt|developer message|api[ _-]?key|secret key)/i,
  /(?:系统提示词|开发者消息|密钥|skill\s*原文|技能原文)/i,
];

export function blocksPromptExtraction(question: string) {
  const normalized = question.normalize("NFKC");
  return promptExtractionPatterns.some((pattern) => pattern.test(normalized));
}
