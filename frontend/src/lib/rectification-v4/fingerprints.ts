import { createHash } from "node:crypto";
import type { CalculationSpec, LifeEventRevision } from "./contracts.ts";
import { latestEventRevisions } from "./evidence-ledger.ts";

function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => [key, canonical(item)]));
  }
  return value;
}

function hash(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(canonical(value))).digest("hex");
}

export function calculationSpecHash(spec: CalculationSpec): string {
  return hash(spec);
}

export function evidenceSetHash(revisions: readonly LifeEventRevision[]): string {
  return hash(latestEventRevisions(revisions).map((event) => ({
    eventId: event.eventId,
    revision: event.revision,
    domain: event.domain,
    eventKind: event.eventKind,
    dateRange: event.dateRange,
    scoreability: event.scoreability,
  })));
}
