# Research Workspace

This directory stores research notes, audits, benchmark packets, and active adjudicator iteration records for the Jyotish project.

## Layout

- `active/`
  - reserved for current working research fronts that directly support the next implementation cycle
- `archive/`
  - historical round notes, sidecar work orders, and local draft research that should not clutter normal implementation work
- top-level `docs/research/*.md`
  - current canonical research notes that are still referenced by active engineering work

## What Stays Top-Level

Keep a research file at the top level only if at least one of the following is true:

- it is referenced by an active implementation spec
- it is referenced by tests, workflow docs, or benchmark dashboards
- it captures a currently active adjudicator audit or closure board

## What Moves To Archive

Move a research file into `archive/` when:

- it is a completed round log or sidecar work order
- it is a local exploration draft with no active code dependency
- it is superseded by a newer audit, dashboard, or implementation note

## Current Working Rule

When adding new research notes:

1. put active, decision-driving notes at the top level
2. move noisy round-by-round drafts into `archive/`
3. avoid storing transient terminal captures or scratch outputs here
