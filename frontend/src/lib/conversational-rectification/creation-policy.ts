export type ConversationalRectificationCreationAudience =
  | "paused"
  | "smoke_only"
  | "public";

export type ConversationalRectificationCreationPolicyInput = Readonly<{
  userId?: string | null;
  creationEnabled?: string;
  migrationsReady?: string;
  deploymentSha?: string;
  smokeSha?: string;
  syntheticSmokeUserIds?: string;
}>;

export type ConversationalRectificationCreationPolicy = Readonly<{
  audience: ConversationalRectificationCreationAudience;
  allowNewCaseCreation: boolean;
  smokeMatchesDeployment: boolean;
}>;

const fullDeploymentSha = /^[0-9a-f]{40}$/;
const canonicalUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export function conversationalRectificationCreationPolicy(
  input: ConversationalRectificationCreationPolicyInput,
): ConversationalRectificationCreationPolicy {
  const deploymentSha = input.deploymentSha?.trim() ?? "";
  const smokeSha = input.smokeSha?.trim() ?? "";
  const baseGatesOpen = input.creationEnabled?.trim().toLowerCase() === "true"
    && input.migrationsReady?.trim().toLowerCase() === "true"
    && fullDeploymentSha.test(deploymentSha);
  if (!baseGatesOpen) {
    return {
      audience: "paused",
      allowNewCaseCreation: false,
      smokeMatchesDeployment: false,
    };
  }

  const smokeMatchesDeployment = smokeSha === deploymentSha;
  if (smokeMatchesDeployment) {
    return {
      audience: "public",
      allowNewCaseCreation: true,
      smokeMatchesDeployment: true,
    };
  }

  const smokeUsers = new Set(
    (input.syntheticSmokeUserIds ?? "")
      .split(",")
      .map((value) => value.trim())
      .filter((value) => canonicalUuid.test(value)),
  );
  if (smokeUsers.size === 0) {
    return {
      audience: "paused",
      allowNewCaseCreation: false,
      smokeMatchesDeployment: false,
    };
  }
  return {
    audience: "smoke_only",
    allowNewCaseCreation: input.userId != null && smokeUsers.has(input.userId),
    smokeMatchesDeployment: false,
  };
}

export function conversationalRectificationCreationPolicyFromEnvironment(
  userId?: string | null,
): ConversationalRectificationCreationPolicy {
  return conversationalRectificationCreationPolicy({
    userId,
    creationEnabled: process.env.RECTIFICATION_V3_CREATE_ENABLED,
    migrationsReady: process.env.RECTIFICATION_V3_MIGRATIONS_READY,
    deploymentSha: conversationalRectificationDeploymentShaFromEnvironment(),
    smokeSha: process.env.RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA,
    syntheticSmokeUserIds: process.env.RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS,
  });
}

export function conversationalRectificationDeploymentShaFromEnvironment(): string {
  return process.env.GITHUB_SHA
    ?? process.env.VERCEL_GIT_COMMIT_SHA
    ?? process.env.NEXT_PUBLIC_GIT_COMMIT
    ?? "unknown";
}
