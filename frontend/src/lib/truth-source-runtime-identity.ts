import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

type OracleSummary = {
  ready: string[];
  partial: string[];
  blocked: string[];
};

export type TruthSourceRuntimeIdentity = {
  status: "ok" | "blocked";
  path: string;
  mountStatus: "mounted" | "not_mounted";
  commit: string;
  skillVersion: string;
  evidencePacketCount: number | null;
  oracleSummary: OracleSummary;
  claimGateStatus: "ready" | "partial_or_blocked_present" | "not_mounted";
};

export const DEFAULT_RESEARCH_TRUTH_SOURCE_PATH = "/Users/wuyongnaren/Documents/印度占星";

function readJson(path: string): unknown {
  return JSON.parse(readFileSync(path, "utf8"));
}

function readEvidencePacketCount(researchPath: string): number | null {
  const indexPath = join(researchPath, "references/oracle/evidence_packet_index_2026_07_19.json");
  if (!existsSync(indexPath)) return null;
  const data = readJson(indexPath) as { summary?: { packet_count?: unknown } };
  return typeof data.summary?.packet_count === "number" ? data.summary.packet_count : null;
}

function readSkillVersion(researchPath: string): string {
  const skillPath = join(researchPath, "SKILL.md");
  if (!existsSync(skillPath)) return "unknown";
  const source = readFileSync(skillPath, "utf8");
  const version = source.match(/(?:version|Version)[:：]\s*([^\n]+)/);
  return version?.[1]?.trim() || "present_unversioned";
}

function readCommit(researchPath: string): string {
  const headPath = join(researchPath, ".git/HEAD");
  if (!existsSync(headPath)) return "unknown";
  const head = readFileSync(headPath, "utf8").trim();
  if (!head.startsWith("ref: ")) return head.slice(0, 40);
  const refPath = join(researchPath, ".git", head.slice(5));
  if (!existsSync(refPath)) return "unknown";
  return readFileSync(refPath, "utf8").trim().slice(0, 40);
}

export function getTruthSourceRuntimeIdentity(
  researchPath = process.env.JYOTISH_RESEARCH_TRUTH_SOURCE_PATH ?? DEFAULT_RESEARCH_TRUTH_SOURCE_PATH,
): TruthSourceRuntimeIdentity {
  if (!existsSync(researchPath)) {
    return {
      status: "blocked",
      path: researchPath,
      mountStatus: "not_mounted",
      commit: "unknown",
      skillVersion: "unknown",
      evidencePacketCount: null,
      oracleSummary: { ready: [], partial: [], blocked: ["research_truth_source_not_mounted"] },
      claimGateStatus: "not_mounted",
    };
  }

  const evidencePacketCount = readEvidencePacketCount(researchPath);
  const blocked = evidencePacketCount === null ? ["evidence_packet_index_missing"] : [];
  const partial = ["commercial_runtime_identity_only"];

  return {
    status: blocked.length ? "blocked" : "ok",
    path: researchPath,
    mountStatus: "mounted",
    commit: readCommit(researchPath),
    skillVersion: readSkillVersion(researchPath),
    evidencePacketCount,
    oracleSummary: { ready: [], partial, blocked },
    claimGateStatus: blocked.length ? "partial_or_blocked_present" : "partial_or_blocked_present",
  };
}
