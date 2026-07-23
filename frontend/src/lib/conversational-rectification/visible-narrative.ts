import type { ConversationalRectificationTurn } from "./contracts.ts";

type EvidenceDomain = NonNullable<
  ConversationalRectificationTurn["evidenceRequest"]
>["domains"][number];

const domainLabels = {
  career: "事业与身份",
  education: "学业与学习",
  finance: "收入与资产",
  health_pressure: "健康与重大压力",
  relocation: "搬迁与居住地",
  relationship: "重要关系",
  family: "家庭变化",
  other: "其他关键经历",
} as const satisfies Readonly<Record<EvidenceDomain, string>>;

function nextEvidenceDomains(turn: ConversationalRectificationTurn): EvidenceDomain[] {
  const provided = new Set(turn.evidenceRecap.flatMap((item) => item.domain ? [item.domain] : []));
  const requested = [...(turn.evidenceRequest?.domains ?? [])];
  const unanswered = requested.filter((domain) => !provided.has(domain));
  return (unanswered.length > 0 ? unanswered : requested).slice(0, 2);
}

export function visibleRectificationNarrative(turn: ConversationalRectificationTurn): string {
  if (turn.narrative.trim()) return turn.narrative;

  const suggestedDomains = nextEvidenceDomains(turn).map((domain) => domainLabels[domain]);
  if (turn.evidenceRecap.length === 0) {
    const examples = suggestedDomains.length > 0
      ? suggestedDomains.join("或")
      : "工作、搬迁、关系或学业";
    return `为了帮助校正出生时间，请先说一件${examples}方面已经发生的重要经历。最好带上年月，直接像聊天一样描述即可。`;
  }

  const latestEvidence = turn.evidenceRecap.at(-1)!;
  if (latestEvidence.dateLabel === "日期待补充") {
    return `你提到“${latestEvidence.summary}”，具体内容我已经记下了。它大致是什么年月？只记得年份也可以。`;
  }
  if (turn.candidate.status === "ready_for_confirmation") {
    return [
      `${latestEvidence.isCorrection ? "已修订" : "已记录"}：${latestEvidence.dateLabel} · ${latestEvidence.summary}。`,
      "目前已经形成一个待确认候选。你可以展开下方详情核对，也可以继续补充一件带年月的真实经历。",
    ].join("\n\n");
  }

  const candidateRange = turn.candidate.rangeStart && turn.candidate.rangeEnd
    ? `${turn.candidate.rangeStart}–${turn.candidate.rangeEnd}`
    : turn.candidate.representativeTime ?? "当前候选范围";
  const nextQuestion = suggestedDomains.length > 0
    ? `接下来请说一件${suggestedDomains.join("或")}方面已经发生的事，尽量带上年月。`
    : "接下来请再说一件已经发生的真实经历，尽量带上年月。";
  return [
    `${latestEvidence.isCorrection ? "已修订" : "已记录"}：${latestEvidence.dateLabel} · ${latestEvidence.summary}。`,
    `候选范围现在是 ${candidateRange}。范围暂未变化不代表提交失败，我会结合后续经历继续比较相邻分钟。`,
    nextQuestion,
  ].join("\n\n");
}
