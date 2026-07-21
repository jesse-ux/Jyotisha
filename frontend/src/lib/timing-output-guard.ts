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

// The boundary is structural: an educational question frame is removed first,
// then a personal subject/context, chart object, and chart predicate must agree.
// This avoids treating every sentence that merely contains `你` and `宫` as a
// personal chart claim.
const chineseZodiacSignSource = String.raw`(?:白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼)`;
const chineseNamedHouseSource = String.raw`(?:命|财帛|兄弟|田宅|子女|夫妻|婚姻|疾厄|迁移|事业|官禄|交友|仆役|福德|父母)宫`;
const chineseChartObjectSource = String.raw`(?:盘面?|星盘|命盘|出生盘|本命盘|D\s*\d+|上升(?:星座)?|星座|${chineseZodiacSignSource}(?:座|上升)|(?:第\s*)?[一二三四五六七八九十百0-9]+\s*宫|${chineseNamedHouseSource}|宫位|行星|星体|太阳|月亮|火星|水星|木星|金星|土星|罗喉|凯图|Rahu|Ketu)`;
const chineseChartObjectPattern = new RegExp(chineseChartObjectSource, "iu");
const chineseChartPredicatePattern = /(?:落(?:在|入|座)?|位于|进入|为|是|有|显示|表明|说明|意味着|主宰|很?强|很?弱|旺|受克|有力|无力|[:：])/iu;
const chineseOwnedChartSubjectPattern = new RegExp(
  String.raw`(?:你|您)\s*(?:的|个人(?:的)?)?\s*${chineseChartObjectSource}`,
  "iu",
);
const chineseUserHasChartPattern = new RegExp(
  String.raw`(?:你|您)\s*(?:为|是|有|拥有)\s*(?:一(?:个|颗)\s*)?${chineseChartObjectSource}`,
  "iu",
);
const chinesePersonalChartContextPattern = /(?:对(?:你|您)而言|基于(?:你|您)(?:的)?(?:盘面?|星盘|命盘|出生盘|本命盘)|在(?:你|您)(?:的)?(?:盘面?|星盘|命盘|出生盘|本命盘)(?:中|里)?)/iu;
const chineseChartAddressesUserPattern = new RegExp(
  String.raw`${chineseChartObjectSource}\s*(?:显示|表明|说明|意味着)[^。！？.!?\n]{0,24}(?:你|您)`,
  "iu",
);

const englishZodiacSignSource = String.raw`(?:aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)`;
const englishChartObjectSource = String.raw`(?:natal\s+chart|birth\s+chart|chart|ascendant|rising(?:\s+sign)?|D\s*\d+(?:\s+chart)?|placement|(?:\d+(?:st|nd|rd|th)|[a-z]+)\s+house|house|planet|sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu)`;
const englishChartObjectPattern = new RegExp(String.raw`\b${englishChartObjectSource}\b`, "iu");
const englishChartPredicatePattern = /(?:\b(?:has|have|is|are|occup(?:y|ies)|falls?|lands?|sits?|placed?|located?|shows?|indicates?|means?|rules?|strong|weak)\b|[:：])/iu;
const englishOwnedChartSubjectPattern = new RegExp(
  String.raw`\b(?:your|the\s+user(?:'s)?)\s+(?:personal\s+)?${englishChartObjectSource}\b`,
  "iu",
);
const englishUserIsOrHasChartPattern = new RegExp(
  String.raw`\byou\s+(?:are|have)\s+(?:an?\s+)?(?:${englishZodiacSignSource}\s+(?:rising|ascendant)|${englishChartObjectSource})\b`,
  "iu",
);
const englishPersonalChartContextPattern = /\b(?:for\s+you|(?:in|from|based\s+on|according\s+to)\s+your\s+(?:natal\s+|birth\s+)?chart)\b/iu;
const englishChartAddressesUserPattern = new RegExp(
  String.raw`\b${englishChartObjectSource}\s+(?:shows?|indicates?|means?)\s+(?:that\s+)?you\b`,
  "iu",
);

const chineseEducationalFramePattern = /^(?:(?:你|您)(?:的)?问题(?:是|为)|(?:你|您)(?:所)?问(?:的)?(?:是)?)[\s,，:：]*/iu;
const chineseAboutGeneralMeaningPattern = /^关于\s*(?:你|您)(?:的)?\s*(.+?(?:一般含义|一般意义))$/iu;
const chineseChartMetaReferencePattern = new RegExp(
  String.raw`${chineseChartObjectSource}\s*(?:(?:的\s*)?一般问题|方面的问题|问题(?:的\s*)?提问者|(?:的\s*)?提问者)`,
  "giu",
);
const englishEducationalFramePattern = /^(?:your\s+question\s+is|you\s+asked\s+about)\s*/iu;

function normalizeClaimClause(clause: string) {
  let normalized = clause
    .normalize("NFKC")
    .replace(/[*_`~]+/gu, "")
    .replace(/\s+/gu, " ")
    .trim();
  normalized = normalized
    .replace(chineseEducationalFramePattern, "")
    .replace(englishEducationalFramePattern, "")
    .replace(chineseChartMetaReferencePattern, "咨询问题");
  const aboutGeneralMeaning = chineseAboutGeneralMeaningPattern.exec(normalized);
  return aboutGeneralMeaning?.[1] ?? normalized;
}

function isPersonalChartConclusion(clause: string) {
  const normalized = normalizeClaimClause(clause);
  const chineseStructure = (chineseOwnedChartSubjectPattern.test(normalized)
      || chineseUserHasChartPattern.test(normalized)
      || chinesePersonalChartContextPattern.test(normalized)
      || chineseChartAddressesUserPattern.test(normalized))
    && chineseChartObjectPattern.test(normalized)
    && chineseChartPredicatePattern.test(normalized);
  const englishStructure = (englishOwnedChartSubjectPattern.test(normalized)
      || englishUserIsOrHasChartPattern.test(normalized)
      || englishPersonalChartContextPattern.test(normalized)
      || englishChartAddressesUserPattern.test(normalized))
    && englishChartObjectPattern.test(normalized)
    && englishChartPredicatePattern.test(normalized);
  return chineseStructure || englishStructure;
}

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
  const guarded = guardPreciseTimingOutput(text);
  return guarded
    .split(/([。！？.!?\n]+)/u)
    .map((part, index) => (
      index % 2 === 0 && isPersonalChartConclusion(part)
        ? GENERAL_NO_BIRTH_TIME_REFUSAL
        : part
    ))
    .join("");
}
