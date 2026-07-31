import { CURRENT_RECTIFICATION_PROMPT_VERSION, CURRENT_RECTIFICATION_SKILL_VERSION } from "./contracts.ts";
import { recordRectificationAgentTelemetry } from "./telemetry.ts";

const skillName = "birth-time-rectification";

type SkillAgent = Readonly<{ getSkill(name: string): Promise<unknown> }>;

export async function assertRectificationSkillLoaded(
  agent: SkillAgent,
  input: Readonly<{ caseId: string; modelId: string | null; deploymentSha: string | null }>,
): Promise<void> {
  const started = Date.now();
  try {
    if (!await agent.getSkill(skillName)) throw new Error("missing");
    recordRectificationAgentTelemetry({
      caseId: input.caseId, phase: "skill", outcome: "succeeded", modelId: input.modelId,
      toolName: null, decisionAction: null, durationMs: Date.now() - started,
      errorCode: null, deploymentSha: input.deploymentSha,
      skillName, skillVersion: CURRENT_RECTIFICATION_SKILL_VERSION,
      promptVersion: CURRENT_RECTIFICATION_PROMPT_VERSION, loadStatus: "loaded",
    });
  } catch {
    recordRectificationAgentTelemetry({
      caseId: input.caseId, phase: "skill", outcome: "failed", modelId: input.modelId,
      toolName: null, decisionAction: null, durationMs: Date.now() - started,
      errorCode: "rectification_skill_not_loaded", deploymentSha: input.deploymentSha,
      skillName, skillVersion: CURRENT_RECTIFICATION_SKILL_VERSION,
      promptVersion: CURRENT_RECTIFICATION_PROMPT_VERSION, loadStatus: "failed",
    });
    throw new Error("rectification_skill_not_loaded");
  }
}
