import { randomUUID } from "node:crypto";
import type { LifeEventRevision } from "./contracts.ts";
import { assertScorerSupports, scoreabilityFor } from "./domain-scorers.ts";

export type NewEventRevision = Omit<LifeEventRevision, "id" | "revision" | "supersedesRevisionId" | "createdAt" | "scoreability"> & {
  readonly scoreability?: LifeEventRevision["scoreability"];
};

export function latestEventRevisions(revisions: readonly LifeEventRevision[]): readonly LifeEventRevision[] {
  const latest = new Map<string, LifeEventRevision>();
  for (const revision of revisions) {
    const current = latest.get(revision.eventId);
    if (!current || revision.revision > current.revision) latest.set(revision.eventId, revision);
  }
  return [...latest.values()].sort((left, right) => left.eventId.localeCompare(right.eventId));
}

export function chronologicalEvents(events: readonly LifeEventRevision[]): readonly LifeEventRevision[] {
  return [...events].sort((left, right) => left.createdAt.localeCompare(right.createdAt)
    || left.eventId.localeCompare(right.eventId)
    || left.revision - right.revision);
}

export function appendEventRevision(
  revisions: readonly LifeEventRevision[],
  input: NewEventRevision,
  options: { readonly now?: Date; readonly id?: string } = {},
): LifeEventRevision {
  const prior = revisions.filter((value) => value.eventId === input.eventId)
    .sort((left, right) => right.revision - left.revision)[0] ?? null;
  const revision: LifeEventRevision = {
    ...input,
    id: options.id ?? randomUUID(),
    revision: (prior?.revision ?? 0) + 1,
    scoreability: input.scoreability ?? scoreabilityFor(input.domain),
    supersedesRevisionId: prior?.id ?? null,
    createdAt: (options.now ?? new Date()).toISOString(),
  };
  assertScorerSupports(revision);
  return revision;
}

export function scoreableEvents(revisions: readonly LifeEventRevision[]): readonly LifeEventRevision[] {
  return latestEventRevisions(revisions).filter((event) => event.scoreability === "scoreable");
}
