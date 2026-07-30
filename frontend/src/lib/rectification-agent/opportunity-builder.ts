import { createHash } from "node:crypto";
import type { CandidateSnapshot, EvidenceDomain, LifeEventRevision, RectificationV4Turn } from "../rectification-v4/contracts.ts";
import { chronologicalEvents } from "../rectification-v4/evidence-ledger.ts";
import type { TargetDisposition } from "../rectification-v4/extraction.ts";
import type { DiagnosticsSummary, QuestionOpportunity, SemanticQuestionOpportunity } from "./contracts.ts";

const forbiddenMoves: SemanticQuestionOpportunity["forbiddenMoves"] = [
  "switch_target_event", "ask_multiple_questions", "claim_exact_birth_minute", "invent_event",
  "invent_date", "expose_private_score", "expose_internal_id", "expose_technique_trace",
];

const domainPolicy: Readonly<Record<Exclude<EvidenceDomain, "family" | "other">, Readonly<{
  goal: (anchor: string | null) => string;
  fallbackPrompt: (anchor: string | null) => string;
  recallCues: string;
  signals: RegExp;
  recallEase: number;
  privacyCost: number;
}>>> = {
  education: {
    goal: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}引导用户回忆一件学习路径变化，用复读、转学、换专业、毕业或重要考试等非穷举线索，不预设一定发生。`,
    fallbackPrompt: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}有没有一件学习路径明显变化的经历，比如复读、转学、换专业、毕业或重要考试改变去向；如果有，大概是哪年哪月，没有或记不清也可以换一类经历？`,
    recallCues: "复读、转学、换专业、毕业或重要考试改变去向",
    signals: /大学|学校|入学|升学|毕业|考试|专业|读书|复读|转学/,
    recallEase: .82,
    privacyCost: .03,
  },
  relocation: {
    goal: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}引导用户回忆一件真正改变居住基地的经历，用搬家、住校或到另一座城市长期生活等非穷举线索，不把当前事件换词重问。`,
    fallbackPrompt: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}有没有一件真正改变居住地点的经历，比如独立搬家、住校或到另一座城市长期生活；如果有，大概是哪年哪月，没有或记不清也可以换一类经历？`,
    recallCues: "独立搬家、住校或到另一座城市长期生活",
    signals: /搬家|搬到|搬去|迁居|迁到|迁往|移居|定居|住校|长期居住|生活基地|离家|外地|异地/,
    recallEase: .78,
    privacyCost: .04,
  },
  relationship: {
    goal: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}在用户愿意的前提下，引导回忆一件关系状态变化，用关系确立、分开、结婚或共同生活等非穷举线索，不预设一定发生。`,
    fallbackPrompt: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}如果你愿意，有没有一件关系状态明显变化的经历，比如关系确立、分开、结婚或开始共同生活；如果有，大概是哪年哪月，没有或不想回答可以换一类经历？`,
    recallCues: "关系确立、分开、结婚或开始共同生活",
    signals: /恋爱|关系|结婚|离婚|分手|伴侣|对象|共同生活/,
    recallEase: .62,
    privacyCost: .22,
  },
  career: {
    goal: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}引导用户回忆一件工作状态变化，用第一次正式入职、离职、换岗、创业或职责增加等非穷举线索，不预设一定发生。`,
    fallbackPrompt: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}有没有一件工作状态明显变化的经历，比如第一次正式入职、离职、换岗、创业或职责明显增加；如果有，大概是哪年哪月，没有或记不清也可以换一类经历？`,
    recallCues: "第一次正式入职、离职、换岗、创业或职责明显增加",
    signals: /工作|实习|公司|研究院|职业|入职|离职|创业|负责|换岗|职责/,
    recallEase: .85,
    privacyCost: .03,
  },
  finance: {
    goal: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}在用户愿意的前提下，引导回忆一件财务结构变化，用收入来源、负债、购房或重大投资等非穷举线索，不预设一定发生。`,
    fallbackPrompt: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}如果方便，有没有一件财务结构明显变化的经历，比如收入来源改变、开始或还清大额负债、购房或重大投资；如果有，大概是哪年哪月，没有或不想回答可以换一类经历？`,
    recallCues: "收入来源改变、开始或还清大额负债、购房或重大投资",
    signals: /收入|负债|投资|资产|财务|买房|卖房|购房/,
    recallEase: .6,
    privacyCost: .18,
  },
  health_pressure: {
    goal: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}在用户愿意的前提下，引导回忆一件本人健康或高压状态变化，用手术、住院、事故、确诊或明显恢复等非穷举线索，不预设一定发生。`,
    fallbackPrompt: (anchor) => `${anchor ? `在“${anchor}”之外，` : ""}如果方便，你本人有没有一件健康或高压状态明显变化的经历，比如手术、住院、事故、确诊或明显恢复；如果有，大概是哪年哪月，没有或不想回答可以换一类经历？`,
    recallCues: "手术、住院、事故、确诊或明显恢复",
    signals: /住院|手术|事故|健康|生病|确诊|康复|高压|恢复/,
    recallEase: .58,
    privacyCost: .28,
  },
};

function stableUuid(value: string): string {
  const hex = createHash("sha256").update(value).digest("hex").slice(0, 32).split("");
  hex[12] = "4";
  hex[16] = ((Number.parseInt(hex[16]!, 16) & 3) | 8).toString(16);
  return `${hex.slice(0, 8).join("")}-${hex.slice(8, 12).join("")}-${hex.slice(12, 16).join("")}-${hex.slice(16, 20).join("")}-${hex.slice(20).join("")}`;
}

const routingValue: Record<QuestionOpportunity["kind"], number> = {
  clarify_intake: .18,
  resolve_event_conflict: .16,
  clarify_event_subject: .14,
  refine_event_date: .08,
  pair_related_event: .05,
  disambiguate_candidate_split: .04,
  ask_new_event: 0,
};

type OpportunityInput = Omit<SemanticQuestionOpportunity, "contractVersion" | "opportunityId" | "utility" | "active" | "forbiddenMoves">;

function utility(value: OpportunityInput): number {
  return Number((
    .35 * value.expectedInformationGain + .20 * value.dateSensitivity + .15 * value.candidateSplitRelevance
    + .10 * value.domainCoverageGain + .10 * value.recallEase + .10 * value.novelty
    + routingValue[value.kind] - value.repetitionPenalty - value.privacyCost
  ).toFixed(6));
}

function opportunity(caseId: string, input: OpportunityInput): QuestionOpportunity {
  return {
    contractVersion: "semantic-question-v2",
    ...input,
    forbiddenMoves,
    opportunityId: stableUuid(`${caseId}:${input.kind}:${input.targetEventId ?? input.domain}:${input.goal}:${input.fallbackPrompt}`),
    utility: utility(input),
    active: true,
  };
}

function daysWide(event: LifeEventRevision): number {
  return Math.floor((Date.parse(`${event.dateRange.end}T00:00:00Z`) - Date.parse(`${event.dateRange.start}T00:00:00Z`)) / 86_400_000) + 1;
}

function anchorFor(event: LifeEventRevision): string {
  return event.summary.replace(/[“”"']/g, "").trim().slice(0, 80);
}

function declinedSensitiveDomains(turns: readonly RectificationV4Turn[]): ReadonlySet<EvidenceDomain> {
  const result = new Set<EvidenceDomain>();
  for (const turn of turns) {
    if (turn.questionDomain && /不想说|不方便说|不想回答|跳过|这个不说|换个方向|不聊这个/.test(turn.answer)) result.add(turn.questionDomain);
  }
  return result;
}

export function buildQuestionOpportunities(input: Readonly<{
  caseId: string;
  events: readonly LifeEventRevision[];
  turns: readonly RectificationV4Turn[];
  snapshot: CandidateSnapshot | null;
  diagnostics: DiagnosticsSummary | null;
  targetDisposition?: TargetDisposition;
  retryTargetEventIds?: readonly string[];
}>): readonly QuestionOpportunity[] {
  const targetAttempts = new Map<string, number>();
  for (const turn of input.turns) {
    if (turn.questionTargetEventId) targetAttempts.set(turn.questionTargetEventId, (targetAttempts.get(turn.questionTargetEventId) ?? 0) + 1);
  }
  const retryTargets = new Set(input.retryTargetEventIds ?? []);
  const scoreableDomains = new Set(input.events.filter((event) => event.scoreability === "scoreable").map((event) => event.domain));
  const refusedDomains = declinedSensitiveDomains(input.turns);
  const latestEvent = chronologicalEvents(input.events).at(-1);
  const latestContext = input.turns.at(-1)?.answer ?? latestEvent?.rawText ?? "";
  const opportunities: QuestionOpportunity[] = [];

  if (input.targetDisposition === "answered_other_event") {
    for (const eventId of retryTargets) {
      const event = input.events.find((value) => value.eventId === eventId);
      if (!event || (targetAttempts.get(eventId) ?? 0) > 1) continue;
      const anchor = anchorFor(event);
      opportunities.push(opportunity(input.caseId, {
        kind: "resolve_event_conflict", domain: event.domain, targetEventId: event.eventId,
        goal: `温和确认“${anchor}”尚缺的日期或主体；允许用户直接跳过。`,
        requestedFields: ["event_range"], anchors: [anchor], contextFacts: [`用户刚补充了另一件完整事件。`, `同一目标最多补问一次。`],
        fallbackPrompt: `关于“${anchor}”，如果还记得大概时间范围，可以补充一下吗？`,
        reason: "用户回答了另一件新事件，原目标只允许一次温和补问。",
        expectedInformationGain: .78, dateSensitivity: .7, candidateSplitRelevance: .55, domainCoverageGain: 0,
        recallEase: .72, novelty: .55, repetitionPenalty: .25, privacyCost: .05,
      }));
    }
  }

  const targetClosed = input.targetDisposition === "unknown"
    || input.targetDisposition === "declined"
    || input.targetDisposition === "direction_change";
  for (const event of input.events) {
    if (targetClosed && retryTargets.has(event.eventId)) continue;
    const attemptCount = targetAttempts.get(event.eventId) ?? 0;
    const anchor = anchorFor(event);
    if ((event.scoreability === "pending_review" || event.subject === "other") && attemptCount === 0) {
      opportunities.push(opportunity(input.caseId, {
        kind: "clarify_event_subject", domain: event.domain, targetEventId: event.eventId,
        goal: `确认“${anchor}”发生在本人、家人还是伴侣。`, requestedFields: ["event_subject"],
        anchors: [anchor], contextFacts: [`当前主体为 ${event.subject}。`],
        fallbackPrompt: `“${anchor}”主要发生在你本人、家人还是伴侣身上？`,
        reason: "事件主体决定是否允许进入个人评分。",
        expectedInformationGain: .9, dateSensitivity: .2, candidateSplitRelevance: .3, domainCoverageGain: .2,
        recallEase: .95, novelty: .9, repetitionPenalty: 0, privacyCost: event.domain === "health_pressure" || event.domain === "family" ? .24 : .05,
      }));
    }
    if (event.scoreability !== "scoreable" || event.dateRange.precision === "day" || attemptCount > 0) continue;
    const sensitivity = input.diagnostics?.eventDateSensitivity.find((item) => item.eventId === event.eventId);
    const dateSensitive = Boolean(sensitivity && (sensitivity.winnerRetentionRate < .65 || sensitivity.candidateClusterRetentionRate < .65));
    const precision = event.dateRange.precision;
    const shouldRefine = precision === "quarter" || precision === "year" || (precision === "month" && dateSensitive)
      || (precision === "range" && daysWide(event) > 120 && dateSensitive);
    if (!shouldRefine) continue;
    const requestedFields: SemanticQuestionOpportunity["requestedFields"] = precision === "year" || precision === "quarter"
      ? ["event_month"]
      : precision === "range" ? ["event_range"] : ["event_day"];
    const fallbackPrompt = precision === "year" || precision === "quarter"
      ? `“${anchor}”大概发生在哪个月，或一年中的哪个时间段？`
      : precision === "range"
        ? `“${anchor}”的时间范围还能再缩小一些吗？`
        : `关于“${anchor}”，你还记得大概哪一天吗？`;
    opportunities.push(opportunity(input.caseId, {
      kind: "refine_event_date", domain: event.domain, targetEventId: event.eventId,
      goal: `仅在必要精度上细化“${anchor}”的日期。`, requestedFields, anchors: [anchor],
      contextFacts: [`现有精度为 ${precision}。`, ...(sensitivity ? [`候选保持率 ${sensitivity.candidateClusterRetentionRate}。`] : [])],
      fallbackPrompt, reason: dateSensitive ? "日期敏感性诊断显示该事件可能改变候选排序。" : "当前日期范围较宽。",
      expectedInformationGain: sensitivity ? 1 - sensitivity.winnerRetentionRate : .66,
      dateSensitivity: sensitivity ? 1 - sensitivity.candidateClusterRetentionRate : .55,
      candidateSplitRelevance: .55, domainCoverageGain: 0, recallEase: precision === "year" ? .8 : .62,
      novelty: .78, repetitionPenalty: 0, privacyCost: .05,
    }));
  }

  const split = input.diagnostics?.candidateSplits[0];
  if (split) {
    const target = input.events.find((event) => split.eventIds.includes(event.eventId)
      && (targetAttempts.get(event.eventId) ?? 0) === 0
      && !(targetClosed && retryTargets.has(event.eventId)));
    const anchor = target ? anchorFor(target) : null;
    opportunities.push(opportunity(input.caseId, {
      kind: "disambiguate_candidate_split", domain: target?.domain ?? "other", targetEventId: target?.eventId ?? null,
      goal: target ? `确认“${anchor}”更接近开始、高峰还是正式结束。` : "确认一件现有事件的发生阶段。",
      requestedFields: ["event_stage"], anchors: anchor ? [anchor] : [],
      contextFacts: [`候选分歧涉及 ${split.techniqueLayers.length} 个已计算技术层。`],
      fallbackPrompt: target ? `“${anchor}”当时更接近事情开始、达到高峰，还是正式结束？` : "那件经历更接近开始、达到高峰，还是正式结束？",
      reason: "候选簇在现有诊断中出现可检验分歧。",
      expectedInformationGain: .88, dateSensitivity: .45, candidateSplitRelevance: .95, domainCoverageGain: 0,
      recallEase: .65, novelty: .9, repetitionPenalty: 0, privacyCost: .1,
    }));
  }

  const scoreableCount = input.events.filter((event) => event.scoreability === "scoreable").length;
  for (const [domain, policy] of Object.entries(domainPolicy) as [Exclude<EvidenceDomain, "family" | "other">, (typeof domainPolicy)[Exclude<EvidenceDomain, "family" | "other">]][]) {
    if (refusedDomains.has(domain)) continue;
    const covered = scoreableDomains.has(domain);
    const latestEventText = latestEvent ? `${latestEvent.summary} ${latestEvent.rawText}` : latestContext;
    const semanticOverlap = Boolean(latestEvent && latestEvent.domain !== domain && policy.signals.test(latestEventText));
    const latestDomainContinuity = latestEvent?.domain === domain ? .22 : 0;
    const pendingThemeBonus = !latestEvent && policy.signals.test(latestContext) ? .12 : 0;
    const alreadyAsked = input.turns.some((turn) => turn.questionDomain === domain && !turn.questionTargetEventId);
    const latestAnchor = latestEvent ? anchorFor(latestEvent) : null;
    opportunities.push(opportunity(input.caseId, {
      kind: "ask_new_event", domain, targetEventId: null, goal: policy.goal(latestAnchor),
      requestedFields: ["new_dated_event"], anchors: latestAnchor ? [latestAnchor] : [],
      contextFacts: [
        `已有 ${scoreableCount} 件可评分事件。`,
        `该领域${covered ? "已有覆盖" : "尚未覆盖"}。`,
        `可使用${policy.recallCues}作为非穷举回忆线索。`,
        "这是存在性询问，不得假定用户一定经历过该事件。",
        "只询问一件带大致年月的新事件，不要求用户逐项回答例子。",
        "允许用户回答没有、记不清、不想回答或换方向。",
        "不得发明年龄或日期窗口，只能引用 anchors 中已确认的经历。",
        ...(semanticOverlap ? ["该领域与最新事件语义重叠，必须降低优先级，避免把同一经历换词重问。"] : []),
      ],
      fallbackPrompt: policy.fallbackPrompt(latestAnchor), reason: covered ? "继续收集可区分候选的独立事件。" : "补足证据领域覆盖。",
      expectedInformationGain: covered ? .54 + latestDomainContinuity + pendingThemeBonus : .65 + pendingThemeBonus,
      dateSensitivity: input.snapshot ? .5 : .35,
      candidateSplitRelevance: input.diagnostics?.candidateSplits.length ? .58 : .42,
      domainCoverageGain: covered ? 0 : scoreableDomains.size < 2 ? 1 : .15,
      recallEase: policy.recallEase, novelty: semanticOverlap ? .45 : alreadyAsked ? .35 : .9,
      repetitionPenalty: (alreadyAsked ? .3 : 0) + (semanticOverlap ? .2 : 0), privacyCost: policy.privacyCost,
    }));
  }

  return opportunities
    .sort((left, right) => right.utility - left.utility || left.opportunityId.localeCompare(right.opportunityId))
    .slice(0, 5);
}
