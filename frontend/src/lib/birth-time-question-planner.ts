export const evidenceDomains = [
  "education", "relocation", "relationship", "career", "finance", "health_pressure",
] as const;

export type EvidenceDomain = (typeof evidenceDomains)[number];
export type EvidenceQuestionPhase = "baseline" | "adaptive";
export type EvidenceDatePrecision = "day" | "month" | "year";

export type CandidateVargaSample = {
  readonly d2Sign?: string | null;
  readonly d4Sign: string | null;
  readonly d9Sign: string | null;
  readonly d10Sign: string | null;
  readonly d24Sign: string | null;
  readonly d30Sign: string | null;
};

export type QuestionPlannerInput = {
  readonly phase: EvidenceQuestionPhase;
  readonly samples: readonly CandidateVargaSample[];
  readonly askedDomains: readonly EvidenceDomain[];
  readonly coveredDomains: readonly EvidenceDomain[];
  readonly adaptiveRound: number;
};

export type QuestionSpec = {
  readonly questionId: string;
  readonly phase: EvidenceQuestionPhase;
  readonly domain: EvidenceDomain;
  readonly requestedPrecision: readonly EvidenceDatePrecision[];
  readonly allowUnknown: true;
  readonly purposeCode: string;
  readonly plannerVersion: string;
};

const layerByDomain = {
  education: "d24Sign",
  relocation: "d4Sign",
  relationship: "d9Sign",
  career: "d10Sign",
  finance: "d2Sign",
  health_pressure: "d30Sign",
} as const;

function questionSpecFor(
  domain: EvidenceDomain,
  phase: EvidenceQuestionPhase,
  adaptiveRound: number,
): QuestionSpec {
  return {
    questionId: `${phase}_${domain}_${adaptiveRound + 1}`,
    phase,
    domain,
    requestedPrecision: ["year", "month"],
    allowUnknown: true,
    purposeCode: `candidate_difference_${domain}`,
    plannerVersion: "candidate-difference-v1",
  };
}

export function planEvidenceQuestion(input: QuestionPlannerInput): QuestionSpec | null {
  const available = evidenceDomains.filter((domain) => !input.askedDomains.includes(domain)
    && (domain !== "finance" || (input.phase === "adaptive" && input.coveredDomains.length >= 2)));
  const ranked = available.map((domain) => ({
    domain,
    split: new Set(input.samples.map((sample) => sample[layerByDomain[domain]]).filter(Boolean)).size,
    coverageBonus: input.coveredDomains.includes(domain) ? 0 : 1,
  })).sort((left, right) => right.split - left.split
    || right.coverageBonus - left.coverageBonus
    || evidenceDomains.indexOf(left.domain) - evidenceDomains.indexOf(right.domain));
  const winner = ranked[0];
  return winner ? questionSpecFor(winner.domain, input.phase, input.adaptiveRound) : null;
}
