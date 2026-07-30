import type { EvidenceDomain, EventKind, LifeEventRevision, Scoreability } from "./contracts.ts";

export type DomainScorerPolicy = Readonly<{
  domain: EvidenceDomain;
  defaultScoreability: Scoreability;
  supportedKinds: readonly EventKind[];
  techniqueLayers: readonly string[];
}>;

export const domainScorerRegistry: Readonly<Record<EvidenceDomain, DomainScorerPolicy>> = {
  education: { domain: "education", defaultScoreability: "scoreable", supportedKinds: ["education_milestone"], techniqueLayers: ["D24", "vimshottari", "narayana"] },
  relocation: { domain: "relocation", defaultScoreability: "scoreable", supportedKinds: ["relocation"], techniqueLayers: ["D4", "vimshottari", "narayana"] },
  relationship: { domain: "relationship", defaultScoreability: "scoreable", supportedKinds: ["relationship_start", "relationship_change"], techniqueLayers: ["D9", "UL", "vimshottari", "narayana"] },
  career: { domain: "career", defaultScoreability: "scoreable", supportedKinds: ["career_change"], techniqueLayers: ["D10", "A10", "vimshottari", "narayana"] },
  finance: { domain: "finance", defaultScoreability: "scoreable", supportedKinds: ["finance_change"], techniqueLayers: ["D2", "D11", "vimshottari", "narayana"] },
  health_pressure: { domain: "health_pressure", defaultScoreability: "scoreable", supportedKinds: ["self_health_event"], techniqueLayers: ["D30", "vimshottari", "narayana"] },
  family: { domain: "family", defaultScoreability: "context_only", supportedKinds: ["family_health_event", "family_bereavement", "family_event"], techniqueLayers: [] },
  other: { domain: "other", defaultScoreability: "pending_review", supportedKinds: ["other"], techniqueLayers: [] },
};

export function scoreabilityFor(domain: EvidenceDomain, eventKind: EventKind, requested?: Scoreability): Scoreability {
  if (domain === "relationship" && eventKind === "relationship_end") return "pending_review";
  return requested ?? domainScorerRegistry[domain].defaultScoreability;
}

export function assertScorerSupports(event: Pick<LifeEventRevision, "domain" | "eventKind" | "scoreability" | "subject">): void {
  const policy = domainScorerRegistry[event.domain];
  if (event.scoreability !== "scoreable") return;
  if (event.subject !== "self" && !(event.domain === "relationship" && event.subject === "partner")) throw new Error("non_self_event_not_scoreable");
  if (!policy.supportedKinds.includes(event.eventKind)) throw new Error("unsupported_event_kind_for_domain");
  if (policy.techniqueLayers.length === 0) throw new Error("domain_not_validated_for_scoring");
}
