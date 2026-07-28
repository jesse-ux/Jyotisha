import { createHash } from "node:crypto";
import { rectificationDeploymentModeSchema, type RectificationDeploymentMode } from "../rectification-v4/contracts.ts";

type RectificationFeatureEnv = Readonly<{
  RECTIFICATION_AGENT_V5_ENABLED?: string;
  RECTIFICATION_AGENT_V5_SHADOW?: string;
  RECTIFICATION_AGENT_V5_CANARY_PERCENT?: string;
}>;

function enabled(value: string | undefined): boolean {
  return /^(1|true|yes|on)$/i.test(value?.trim() ?? "");
}

function percentage(value: string | undefined): number {
  if (!value?.trim()) return 100;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return 0;
  return Math.max(0, Math.min(100, parsed));
}

export function rectificationCanaryBucket(stableId: string): number {
  const prefix = createHash("sha256").update(stableId).digest().readUInt32BE(0);
  return prefix / 0x1_0000_0000 * 100;
}

export function selectRectificationDeploymentMode(
  stableId: string,
  env: RectificationFeatureEnv = {
    RECTIFICATION_AGENT_V5_ENABLED: process.env.RECTIFICATION_AGENT_V5_ENABLED,
    RECTIFICATION_AGENT_V5_SHADOW: process.env.RECTIFICATION_AGENT_V5_SHADOW,
    RECTIFICATION_AGENT_V5_CANARY_PERCENT: process.env.RECTIFICATION_AGENT_V5_CANARY_PERCENT,
  },
): RectificationDeploymentMode {
  if (!enabled(env.RECTIFICATION_AGENT_V5_ENABLED)) return "v4_legacy";
  if (rectificationCanaryBucket(stableId) >= percentage(env.RECTIFICATION_AGENT_V5_CANARY_PERCENT)) return "v4_legacy";
  return rectificationDeploymentModeSchema.parse(
    enabled(env.RECTIFICATION_AGENT_V5_SHADOW) ? "v5_shadow" : "v5_agent",
  );
}
