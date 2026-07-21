import type {
  OnboardingClaimCommand,
  OnboardingCompletionCommand,
  OnboardingProfileRepository,
  OnboardingProfileRow,
} from "../src/lib/onboarding-post.ts";

type ProfilePatch = Partial<Omit<OnboardingProfileRow, "id">>;

export class StatefulOnboardingProfileRepository implements OnboardingProfileRepository {
  private row: OnboardingProfileRow;
  private nextClaimInterference: ProfilePatch | null = null;

  constructor(row: OnboardingProfileRow) {
    this.row = structuredClone(row);
  }

  setProfile(patch: ProfilePatch): void {
    this.row = { ...this.row, ...structuredClone(patch) };
  }

  interfereBeforeNextClaim(patch: ProfilePatch): void {
    this.nextClaimInterference = structuredClone(patch);
  }

  snapshot(): OnboardingProfileRow {
    return structuredClone(this.row);
  }

  async loadProfile(userId: string) {
    return this.row.id === userId
      ? { data: this.snapshot(), error: null }
      : { data: null, error: null };
  }

  async claimProfile(command: OnboardingClaimCommand) {
    if (this.nextClaimInterference) {
      this.setProfile(this.nextClaimInterference);
      this.nextClaimInterference = null;
    }
    const ownsObservedRow = this.row.id === command.userId
      && this.row.onboarding_version === command.expectedVersion
      && this.row.onboarding_generated_at === command.expectedGeneratedAt;
    if (!ownsObservedRow) return { data: null, error: null };

    this.row = {
      ...this.row,
      onboarding_version: command.pendingVersion,
      onboarding_generated_at: command.claimedAt,
    };
    return { data: { id: this.row.id }, error: null };
  }

  async completeProfile(command: OnboardingCompletionCommand) {
    const ownsPendingRow = this.row.id === command.userId
      && this.row.onboarding_version === command.expectedPendingVersion;
    if (!ownsPendingRow) return { data: null, error: null };

    this.row = {
      ...this.row,
      onboarding_payload: structuredClone(command.payload),
      onboarding_version: command.readyVersion,
      onboarding_generated_at: command.generatedAt,
    };
    return { data: { id: this.row.id }, error: null };
  }
}

export function completeProfileRow(
  patch: ProfilePatch = {},
): OnboardingProfileRow {
  return {
    id: "07e583fc-90b9-4fcb-a9d3-8de654eeac9a",
    name: "林遥",
    birth_date: "1990-06-15",
    birth_time: "12:30",
    reported_birth_time: "12:30",
    active_birth_time: "12:30",
    birth_time_source: "legacy_import",
    birth_time_period: null,
    birth_time_clue: null,
    uncertainty_before_minutes: null,
    uncertainty_after_minutes: null,
    birth_time_status: "confirmed",
    country_code: "CN",
    province_code: "110000",
    city_code: "110100",
    onboarding_payload: null,
    onboarding_version: null,
    onboarding_generated_at: null,
    ...structuredClone(patch),
  };
}
