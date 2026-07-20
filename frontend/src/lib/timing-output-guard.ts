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

const personalChartClaimMarkers = [
  String.raw`(?:基于|根据|从|结合)\s*(?:你|您)\s*(?:的\s*)?(?:个人\s*)?(?:星盘|命盘|出生盘|本命盘|盘)`,
  String.raw`(?:你|您)\s*的\s*(?:(?:D\s*\d+)(?:\s*上升)?|上升(?:星座)?|月亮星座|太阳星座|太阳|月亮|火星|水星|木星|金星|土星|罗喉|凯图|Rahu|Ketu|第\s*[一二三四五六七八九十百0-9]+\s*宫|星盘|命盘|出生盘|本命盘|盘)`,
  String.raw`(?:你|您)\s*(?:的\s*)?(?:(?:D\s*\d+)(?:\s*上升)?|上升(?:星座)?|月亮星座|太阳星座|太阳|月亮|火星|水星|木星|金星|土星|罗喉|凯图|Rahu|Ketu|第\s*[一二三四五六七八九十百0-9]+\s*宫|星盘|命盘|本命盘|盘)\s*(?:(?:一定|必然|肯定|必定|绝对)\s*)?(?:是|在|落(?:在|入)?|位于|显示|表明|说明|意味着|主宰)`,
  String.raw`(?:你|您)\s*(?:的\s*)?(?:星盘|命盘|出生盘|本命盘|盘)\s*(?:中|里|内)`,
  String.raw`(?:D\s*\d+|上升(?:星座)?)\s*(?:显示|表明|说明|意味着)\s*(?:你|您)`,
  String.raw`(?:your|the user's)\s+(?:natal\s+|birth\s+)?(?:chart|ascendant|D\s*\d+|\d+(?:st|nd|rd|th)\s+house)`,
];

const personalChartClaimPatterns = personalChartClaimMarkers.map((marker) => new RegExp(
  String.raw`(^|[。！？.!?\n])[^。！？.!?\n]*${marker}[^。！？.!?\n]*`,
  "giu",
));

export const GENERAL_NO_BIRTH_TIME_REFUSAL =
  "当前一般咨询模式不能生成个人星盘结论；你可以改问一般知识，或先完成生时校正";

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

/** A deterministic post-model boundary for the zero-chart general mode. */
export function guardGeneralNoBirthTimeOutput(text: string) {
  let guarded = guardPreciseTimingOutput(text);
  for (const pattern of personalChartClaimPatterns) {
    guarded = guarded.replace(pattern, (_sentence, prefix: string) => (
      `${prefix}${GENERAL_NO_BIRTH_TIME_REFUSAL}`
    ));
  }
  return guarded;
}
