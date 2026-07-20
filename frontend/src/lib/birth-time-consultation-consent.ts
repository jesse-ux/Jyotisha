import { isBirthClockTime, type BirthTimeDraft } from "./birth-time-intake-model.ts";
import type { ConsultationBirthTimeMode } from "./consultation-birth-time-mode.ts";

export type BirthTimeConsultationConsentMode = Extract<
  ConsultationBirthTimeMode,
  "unverified_birth_time" | "general_no_birth_time"
>;

export type BirthTimeConsultationConsentState = Readonly<
  Record<string, BirthTimeConsultationConsentMode>
>;

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
  return consultationModeForSession(state, sessionId) !== null;
}

export function consultationModeForSession(
  state: BirthTimeConsultationConsentState,
  sessionId: string,
): BirthTimeConsultationConsentMode | null {
  if (!sessionId) return null;
  const mode = state[sessionId];
  return mode === "unverified_birth_time" || mode === "general_no_birth_time"
    ? mode
    : null;
}

export function grantBirthTimeConsultationConsent(
  state: BirthTimeConsultationConsentState,
  sessionId: string,
  mode: BirthTimeConsultationConsentMode = "unverified_birth_time",
): BirthTimeConsultationConsentState {
  if (!sessionId || state[sessionId] === mode) return state;
  return Object.freeze({ ...state, [sessionId]: mode });
}

export function clearBirthTimeConsultationConsent(
  state: BirthTimeConsultationConsentState,
  sessionId: string,
): BirthTimeConsultationConsentState {
  if (!sessionId || !state[sessionId]) return state;
  return Object.freeze(Object.fromEntries(
    Object.entries(state).filter(([candidate]) => candidate !== sessionId),
  ) as Record<string, BirthTimeConsultationConsentMode>);
}

export function unverifiedBirthTime(profile: BirthTimeDraft): string | null {
  if (profile.birthTimeStatus === "confirmed") return null;
  if (!concreteReportedSources.has(profile.birthTimeSource)) return null;
  return isBirthClockTime(profile.reportedTime) ? profile.reportedTime : null;
}

export function canUseUnverifiedBirthTime(profile: BirthTimeDraft): boolean {
  return unverifiedBirthTime(profile) !== null;
}

export function requiresBirthTimeConsent(profile: BirthTimeDraft): boolean {
  return canUseUnverifiedBirthTime(profile);
}

export type BirthTimeConsultationRoute =
  | Readonly<{ kind: "choice"; canUseUnverifiedTime: boolean }>
  | Readonly<{
    kind: "consult";
    mode: ConsultationBirthTimeMode;
    time: string | null;
  }>;

export function resolveBirthTimeConsultationRoute(
  profile: BirthTimeDraft,
  state: BirthTimeConsultationConsentState,
  sessionId: string,
): BirthTimeConsultationRoute {
  if (profile.birthTimeStatus === "confirmed" && isBirthClockTime(profile.time)) {
    return { kind: "consult", mode: "verified_chart", time: profile.time };
  }
  const reportedTime = unverifiedBirthTime(profile);
  const consentMode = consultationModeForSession(state, sessionId);
  if (reportedTime && consentMode === "unverified_birth_time") {
    return { kind: "consult", mode: "unverified_birth_time", time: reportedTime };
  }
  if (!reportedTime && consentMode === "general_no_birth_time") {
    return { kind: "consult", mode: "general_no_birth_time", time: null };
  }
  return { kind: "choice", canUseUnverifiedTime: reportedTime !== null };
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

export type LatestAccountRequestGuard = Readonly<{
  begin(): number;
  isCurrent(identity: number): boolean;
}>;

export function createLatestAccountRequestGuard(): LatestAccountRequestGuard {
  let version = 0;
  return Object.freeze({
    begin() {
      version += 1;
      return version;
    },
    isCurrent(identity: number) {
      return identity === version;
    },
  });
}
