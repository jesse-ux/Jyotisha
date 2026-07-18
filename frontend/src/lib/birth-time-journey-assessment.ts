import type {
  JourneyScanInput,
  LegacyBirthTimeJourneyEngine,
  RectificationQuestionnaire,
} from "./birth-time-journey-service.ts";
import type {
  BirthTimeAssessment,
  ScanStability,
} from "./birth-time-journey.ts";

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

function questionnaireStability(
  questionnaire: RectificationQuestionnaire,
): ScanStability {
  if (questionnaire.samples.length < 2) return { kind: "unavailable" };
  const signatures = questionnaire.samples.map((sample) => {
    if (!sample.ascendantSign || !sample.d9Sign || !sample.d10Sign) return null;
    return `${sample.ascendantSign}|${sample.d9Sign}|${sample.d10Sign}`;
  });
  if (signatures.some((signature) => signature === null)) return { kind: "unavailable" };
  return new Set(signatures).size === 1 ? { kind: "stable" } : { kind: "sensitive" };
}

export async function scanAssessment(
  engine: Pick<LegacyBirthTimeJourneyEngine, "scan">,
  assessment: BirthTimeAssessment,
): Promise<{
  readonly stability: ScanStability;
  readonly questionnaire: RectificationQuestionnaire | null;
}> {
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
