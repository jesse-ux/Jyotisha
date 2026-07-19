const exactTimingPatterns = [
  /\b(?:19|20)\d{2}[-/.年]\s?\d{1,2}(?:[-/.月]\s?\d{1,2}(?:日|号)?)?\b/g,
  /\b(?:19|20)\d{2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+\d{1,2})?\b/gi,
  /\b\d{1,2}\/\d{1,2}\/(?:\d{2}|\d{4})\b/g,
  /(?:今年|明年|后年|(?:19|20)\d{2}年)?\s*\d{1,2}月(?:\s*\d{1,2}[日号])?/g,
  /\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:,\s*(?:19|20)\d{2})?\b/gi,
];

const guaranteeConclusionPatterns = [
  /(?:^|[。！？.!?\n])[^。！？.!?\n]*(?:一定|必然|保证|肯定|必定|注定|绝对)(?:会|能|将|发生|成功|结婚|复合|怀孕|发财|升职|得到|实现|出现)[^。！？.!?\n]*/g,
  /(?:^|[.?!\n])[^.?!\n]*\b(?:will definitely|guaranteed? to|certain to|without doubt)\b[^.?!\n]*/gi,
];

/** Removes claims the evidence contract does not permit the model to make. */
export function guardPreciseTimingOutput(text: string) {
  let guarded = text;
  for (const pattern of exactTimingPatterns)
    guarded = guarded.replace(pattern, "[具体时间已省略]");
  for (const pattern of guaranteeConclusionPatterns) {
    guarded = guarded.replace(pattern, (sentence) => {
      const prefix = /^[。！？.!?\n]/.exec(sentence)?.[0] ?? "";
      return prefix + "[保证性结论已省略]";
    });
  }
  return guarded;
}
