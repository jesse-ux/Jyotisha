import type { BirthTimeDraft } from "./birth-time-intake-model.ts";

export type BirthTimeConsultationConsentState = Readonly<Record<string, true>>;

export type AccountRectificationCaseState = Readonly<{
  caseId: string;
  journeyProtocol: "conversational-evidence-v3";
  status: "starting" | "active" | "paused" | "confirming" | "completed" | "abandoned";
  turnVersion: number;
  isRevision: boolean;
  preservesActiveTime: boolean;
}>;

export type RectificationCardAction = "start" | "resume" | "revise";

const concreteReportedSources = new Set<BirthTimeDraft["birthTimeSource"]>([
  "hospital_record",
  "family_exact",
  "approximate",
]);

const unfinishedRectificationStatuses = new Set<AccountRectificationCaseState["status"]>([
  "starting",
  "active",
  "paused",
  "confirming",
]);

export function createBirthTimeConsultationConsentState(): BirthTimeConsultationConsentState {
  return Object.freeze({});
}

export function hasBirthTimeConsultationConsent(
  state: BirthTimeConsultationConsentState,
  sessionId: string,
): boolean {
  return Boolean(sessionId && state[sessionId] === true);
}

export function grantBirthTimeConsultationConsent(
  state: BirthTimeConsultationConsentState,
  sessionId: string,
): BirthTimeConsultationConsentState {
  if (!sessionId || state[sessionId]) return state;
  return Object.freeze({ ...state, [sessionId]: true });
}

export function clearBirthTimeConsultationConsent(
  state: BirthTimeConsultationConsentState,
  sessionId: string,
): BirthTimeConsultationConsentState {
  if (!sessionId || !state[sessionId]) return state;
  return Object.freeze(Object.fromEntries(
    Object.entries(state).filter(([candidate]) => candidate !== sessionId),
  ) as Record<string, true>);
}

export function unverifiedBirthTime(profile: BirthTimeDraft): string | null {
  if (profile.birthTimeStatus === "confirmed") return null;
  if (!concreteReportedSources.has(profile.birthTimeSource)) return null;
  const time = profile.time || profile.reportedTime;
  return /^([01]\d|2[0-3]):[0-5]\d$/.test(time) ? time : null;
}

export function canUseUnverifiedBirthTime(profile: BirthTimeDraft): boolean {
  return unverifiedBirthTime(profile) !== null;
}

export function requiresBirthTimeConsent(profile: BirthTimeDraft): boolean {
  return canUseUnverifiedBirthTime(profile);
}

export function resolveRectificationCardAction(input: Readonly<{
  rectificationCase: AccountRectificationCaseState | null;
  hasConfirmedBirthTime: boolean;
}>): RectificationCardAction {
  if (input.rectificationCase
    && unfinishedRectificationStatuses.has(input.rectificationCase.status)) {
    return "resume";
  }
  if (input.hasConfirmedBirthTime) return "revise";
  return "start";
}

export function parseRectificationPriceCredits(raw: string | undefined): number {
  if (raw === undefined) return 1;
  const normalized = raw.trim();
  if (!/^\d+$/.test(normalized)) {
    throw new Error("RECTIFICATION_PRICE_CREDITS must be an integer from 1 through 100");
  }
  const price = Number(normalized);
  if (!Number.isSafeInteger(price) || price < 1 || price > 100) {
    throw new Error("RECTIFICATION_PRICE_CREDITS must be an integer from 1 through 100");
  }
  return price;
}
