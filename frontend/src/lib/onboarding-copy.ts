const protectedPhrases = [
  "升学、转学或学习方向变化",
  "关系结束或关系明显转变",
  "不会自动补猜缺失时间",
  "带日期的关键经历",
  "当前排盘使用时间",
  "关系明显转变",
  "一个具体时间",
  "候选代表时间",
  "学习方向变化",
  "学习环境变化",
  "真实出生分钟",
  "原始填报时间",
  "你出生在哪里",
  "关系进入",
  "关系结束",
  "当前证据",
  "可以调整",
  "关键经历",
  "具体时间",
  "不确定",
  "证据",
  "以及",
].sort((left, right) => right.length - left.length);

const protectedPhrasePattern = new RegExp(
  `前后\\s+\\d+\\s+分钟|${protectedPhrases.join("|")}`,
  "g",
);

function joinPhrase(phrase: string) {
  return Array.from(phrase.replaceAll(" ", "\u00a0")).join("\u2060");
}

export function protectOnboardingPhrases(text: string) {
  return text.replace(protectedPhrasePattern, joinPhrase);
}
