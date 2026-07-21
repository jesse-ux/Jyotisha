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

// The boundary is structural: first require a personalized subject, then a
// chart object and a placement/conclusion predicate. Planet names are a finite
// vocabulary supplement, not the primary detection mechanism.
const chineseChartObjectPattern = /(?:盘面?|星盘|命盘|出生盘|本命盘|D\s*\d+|上升(?:星座)?|[\p{Script=Han}A-Za-z0-9]{0,8}宫|行星|星体|太阳|月亮|火星|水星|木星|金星|土星|罗喉|凯图|Rahu|Ketu)/iu;
const chineseChartConclusionPattern = /(?:落(?:在|入|座)?|位于|进入|是|在|显示|表明|说明|意味着|主宰|很?强|很?弱|旺|受克|有力|无力|[:：])/iu;
const englishChartObjectPattern = /\b(?:natal\s+chart|birth\s+chart|chart|ascendant|rising\s+sign|D\s*\d+|(?:\d+(?:st|nd|rd|th)|[a-z]+)\s+house|house|planet|sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu)\b/iu;
const englishChartConclusionPattern = /(?:\b(?:is|are|falls?|lands?|sits?|placed?|located?|shows?|indicates?|means?|rules?|strong|weak)\b|[:：])/iu;
const chinesePossessiveChartSubjectPattern = /(?:你|您)\s*(?:的|个人(?:的)?)\s*(?:盘面?|星盘|命盘|出生盘|本命盘|D\s*\d+|上升(?:星座)?|[\p{Script=Han}A-Za-z0-9]{0,8}宫|行星|星体|太阳|月亮|火星|水星|木星|金星|土星|罗喉|凯图|Rahu|Ketu)/iu;
const chineseBareChartSubjectPattern = /(?:你|您)\s*(?:盘面?|星盘|命盘|出生盘|本命盘|D\s*\d+|上升(?:星座)?|(?:第\s*)?[一二三四五六七八九十百0-9]+\s*宫|行星|星体|太阳|月亮|火星|水星|木星|金星|土星|罗喉|凯图|Rahu|Ketu)/iu;
const chineseChartAddressesUserPattern = /(?:盘面?|星盘|命盘|出生盘|本命盘|D\s*\d+|上升(?:星座)?)\s*(?:显示|表明|说明|意味着)\s*(?:你|您)/iu;
const englishPersonalChartSubjectPattern = /\b(?:your|the\s+user(?:'s)?)\s+(?:personal\s+)?(?:natal\s+chart|birth\s+chart|chart|ascendant|rising\s+sign|D\s*\d+|(?:\d+(?:st|nd|rd|th)|[a-z]+)\s+house|house|planet|sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu)\b/iu;
const englishChartAddressesUserPattern = /\b(?:the\s+)?(?:natal\s+|birth\s+)?chart\s+(?:shows?|indicates?|means?)\s+(?:that\s+)?you\b/iu;

function isPersonalChartConclusion(clause: string) {
  const normalized = clause.normalize("NFKC");
  const chineseStructure = (chinesePossessiveChartSubjectPattern.test(normalized)
      || chineseBareChartSubjectPattern.test(normalized)
      || chineseChartAddressesUserPattern.test(normalized))
    && chineseChartObjectPattern.test(normalized)
    && chineseChartConclusionPattern.test(normalized);
  const englishStructure = (englishPersonalChartSubjectPattern.test(normalized)
      || englishChartAddressesUserPattern.test(normalized))
    && englishChartObjectPattern.test(normalized)
    && englishChartConclusionPattern.test(normalized);
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
