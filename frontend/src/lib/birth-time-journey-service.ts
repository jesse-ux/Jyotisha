import {
  assessBirthTime,
  withRectificationScoring,
  type BirthTimeAssessment,
  type JourneySnapshot,
  type RectificationScoring,
  type ScanStability,
} from "./birth-time-journey.ts";

export type RectificationAnswer = "A" | "B" | "C" | "D";

export type RectificationQuestionnaire = {
  readonly questions: readonly {
    readonly id: string;
    readonly prompt: string;
    readonly options?: readonly {
      readonly key: RectificationAnswer;
      readonly label: string;
    }[];
  }[];
  readonly samples: readonly {
    readonly ascendantSign: string | null;
    readonly d9Sign: string | null;
    readonly d10Sign: string | null;
  }[];
  readonly raw: Readonly<Record<string, unknown>>;
};

export type JourneyScanInput = {
  readonly birthTime: string;
  readonly uncertaintyMinutes: number;
  readonly lat: number;
  readonly lon: number;
  readonly tz: number;
  readonly ayanamsa: "lahiri";
};

export type JourneyScoreInput = {
  readonly questionnaire: RectificationQuestionnaire;
  readonly answers: Readonly<Record<string, RectificationAnswer>>;
};

export interface BirthTimeJourneyEngine {
  scan(input: JourneyScanInput): Promise<{ readonly questionnaire: RectificationQuestionnaire }>;
  score(input: JourneyScoreInput): Promise<RectificationScoring & { readonly raw: Readonly<Record<string, unknown>> }>;
}

export type PersistedJourneyAssessment = {
  readonly userId: string;
  readonly assessment: BirthTimeAssessment;
  readonly snapshot: JourneySnapshot;
  readonly questionnaire: RectificationQuestionnaire | null;
  readonly candidateScan: RectificationQuestionnaire | null;
};

export type StoredRectificationCase = {
  readonly id: string;
  readonly userId: string;
  readonly snapshot: JourneySnapshot;
  readonly questionnaire: RectificationQuestionnaire | null;
  readonly answers: Readonly<Record<string, RectificationAnswer>>;
  readonly scoring?: RectificationScoring & { readonly raw: Readonly<Record<string, unknown>> };
};

export interface BirthTimeJourneyStore {
  saveAssessment(value: PersistedJourneyAssessment): Promise<string>;
  loadCase(userId: string, caseId: string): Promise<StoredRectificationCase | null>;
  saveScoring(value: StoredRectificationCase): Promise<void>;
}

type BirthTimeJourneyPorts = {
  readonly store: BirthTimeJourneyStore;
  readonly engine: BirthTimeJourneyEngine;
};

type JourneyResponse = {
  readonly caseId: string;
  readonly snapshot: JourneySnapshot;
  readonly questionnaire: RectificationQuestionnaire | null;
  readonly scoring: (RectificationScoring & { readonly raw: Readonly<Record<string, unknown>> }) | null;
  readonly answers: Readonly<Record<string, RectificationAnswer>>;
};

export class RectificationCaseNotFoundError extends Error {
  readonly name = "RectificationCaseNotFoundError";
  readonly caseId: string;

  constructor(caseId: string) {
    super(`Rectification case ${caseId} was not found`);
    this.caseId = caseId;
  }
}

export class RectificationQuestionsUnavailableError extends Error {
  readonly name = "RectificationQuestionsUnavailableError";
}

function scanInput(assessment: BirthTimeAssessment): JourneyScanInput | null {
  if (assessment.source === "unknown") return null;
  if (assessment.source === "period_only") {
    const periodScan = {
      early_morning: { time: "06:00", uncertainty: 120 },
      morning: { time: "10:00", uncertainty: 120 },
      afternoon: { time: "15:00", uncertainty: 180 },
      evening: { time: "20:30", uncertainty: 150 },
      late_night: { time: "01:30", uncertainty: 150 },
    } as const;
    const scan = periodScan[assessment.period];
    return {
      birthTime: `${assessment.date} ${scan.time}`,
      uncertaintyMinutes: scan.uncertainty,
      lat: assessment.location.lat,
      lon: assessment.location.lon,
      tz: assessment.location.tz,
      ayanamsa: "lahiri",
    };
  }
  return {
    birthTime: `${assessment.date} ${assessment.reportedTime}`,
    uncertaintyMinutes: Math.max(
      assessment.uncertaintyBeforeMinutes,
      assessment.uncertaintyAfterMinutes,
    ),
    lat: assessment.location.lat,
    lon: assessment.location.lon,
    tz: assessment.location.tz,
    ayanamsa: "lahiri",
  };
}

function questionnaireStability(questionnaire: RectificationQuestionnaire): ScanStability {
  if (questionnaire.samples.length < 2) return { kind: "unavailable" };
  const signatures = questionnaire.samples.map((sample) => {
    if (!sample.ascendantSign || !sample.d9Sign || !sample.d10Sign) return null;
    return `${sample.ascendantSign}|${sample.d9Sign}|${sample.d10Sign}`;
  });
  if (signatures.some((signature) => signature === null)) return { kind: "unavailable" };
  return new Set(signatures).size === 1 ? { kind: "stable" } : { kind: "sensitive" };
}

async function scanAssessment(
  engine: BirthTimeJourneyEngine,
  assessment: BirthTimeAssessment,
): Promise<{ readonly stability: ScanStability; readonly questionnaire: RectificationQuestionnaire | null }> {
  const input = scanInput(assessment);
  if (!input) return { stability: { kind: "not_required" }, questionnaire: null };
  try {
    const result = await engine.scan(input);
    return {
      stability: questionnaireStability(result.questionnaire),
      questionnaire: result.questionnaire,
    };
  } catch (error) {
    if (error instanceof Error) {
      return { stability: { kind: "unavailable" }, questionnaire: null };
    }
    throw error;
  }
}

export function createBirthTimeJourneyService(ports: BirthTimeJourneyPorts) {
  return {
    async assess(userId: string, assessment: BirthTimeAssessment): Promise<JourneyResponse> {
      const scan = await scanAssessment(ports.engine, assessment);
      const snapshot = assessBirthTime(assessment, scan.stability);
      const persisted = {
        userId,
        assessment,
        snapshot,
        questionnaire: scan.questionnaire,
        candidateScan: scan.questionnaire,
      } satisfies PersistedJourneyAssessment;
      const caseId = await ports.store.saveAssessment(persisted);
      return { caseId, snapshot, questionnaire: scan.questionnaire, scoring: null, answers: {} };
    },

    async resume(userId: string, caseId: string): Promise<JourneyResponse> {
      const stored = await ports.store.loadCase(userId, caseId);
      if (!stored) throw new RectificationCaseNotFoundError(caseId);
      return {
        caseId,
        snapshot: stored.snapshot,
        questionnaire: stored.questionnaire,
        scoring: stored.scoring ?? null,
        answers: stored.answers,
      };
    },

    async answerQuestion(
      userId: string,
      caseId: string,
      questionId: string,
      answer: RectificationAnswer,
    ): Promise<JourneyResponse> {
      const stored = await ports.store.loadCase(userId, caseId);
      if (!stored) throw new RectificationCaseNotFoundError(caseId);
      if (!stored.questionnaire) throw new RectificationQuestionsUnavailableError();
      const answers = { ...stored.answers, [questionId]: answer };
      const scoring = await ports.engine.score({ questionnaire: stored.questionnaire, answers });
      const snapshot = withRectificationScoring(stored.snapshot, scoring);
      const updated = { ...stored, answers, scoring, snapshot } satisfies StoredRectificationCase;
      await ports.store.saveScoring(updated);
      return { caseId, snapshot, questionnaire: stored.questionnaire, scoring, answers };
    },
  };
}
