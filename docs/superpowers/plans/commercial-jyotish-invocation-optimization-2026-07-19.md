# Commercial Jyotish Invocation Optimization Plan

## Scope

This plan optimizes the commercial repository's actual Jyotish skill execution and the results returned to paying users. It does not modify, reorganize, or treat the research repository as a runtime dependency. Generic frontend, account, billing, and deployment work is out of scope unless it directly prevents an astrology capability from being invoked, verified, or truthfully surfaced.

## Verified Runtime Chain

```text
POST /api/consult
  -> getJyotishAgent(model)
  -> consultationTool / runConsultationWorkflow
  -> POST ${JYOTISH_API_BASE}/api/consultation_workflow
  -> JyotishHandler._compute_consultation_workflow
  -> UnifiedConsultationOrchestrator route selection + strict workflow
  -> chart/evidence/technique/dasha/oracle layers
  -> consumer_context + auditable response
  -> language model renders the bounded user answer
```

Other live product paths:

- Daily guidance: `frontend/src/app/api/daily-starlanguage/route.ts` -> Python `/api/chart` and daily guidance logic.
- Synastry: `frontend/src/app/api/synastry/route.ts` -> Python `/api/chart` for both charts and `/api/synastry`.
- Birth-time flows call the bounded guide/rectification routes and must not obtain unrestricted consultation authority.

Verified baseline:

- `python3 scripts/user_invocation_acceptance_check.py`: pass. Strict routes available: career, relationship, finance.
- Core API and external adapters are available; the official VedAstro snapshot is not ready in this environment (`fast_local_fallback`, premium key absent). This is an explicit degraded external layer, not a failed local calculation.
- `skills/jyotish-vedic-astrology/SKILL.md` exists and is the default Mastra skill path.
- The Python server has many registered endpoints, but only the paths above are currently commercial-user reachable. Registered-but-unreachable techniques are not treated as product capability.

## Non-Negotiable Product Truth Rules

1. A user-facing claim must originate from a computed invocation result, never from an LLM choosing to improvise chart facts.
2. For career, relationship, wealth, timing, health, or event claims, the returned evidence must contain the domain-required strict workflow layers and an explicit status for every missing layer.
3. The commercial response may simplify language, but it may not drop a `blocked`, `degraded`, conflict, ayanamsa/node-mode, Dasha-boundary, functional-benefic/malefic, or external-evidence limitation that materially changes the claim.
4. Local engine success, external-engine availability, executed raw coverage, parity, and predictive calibration remain separate states. No response upgrades one state into another.
5. No research checkout/path, raw private case, oracle credential, or unapproved source artifact becomes a commercial runtime dependency.

## Phase 0: Make Invocation Deterministic

### Problem

The chat agent receives instructions to call `consultationTool`, but model tool choice is probabilistic. An instruction-level requirement is not a server-side guarantee that a new chart claim has traversed the Jyotish engine.

### Work

1. Extract a deterministic `requiresJyotishWorkflow(question, profile, conversationState)` classifier in the commercial server layer.
2. For a new chart claim, call `runConsultationWorkflow` before streaming model output, then inject only the validated `consumer_context`/evidence projection into the agent. Do not depend on the model to decide whether to call the tool.
3. Preserve tool use for follow-ups only when the stored invocation result covers the request; otherwise re-run the workflow with an explicit reason.
4. Add an invocation receipt to the stream metadata: immutable request ID, workflow version, route, entry mode, local/external status, and evidence-packet ID. Never include birth data, question text, prompts, or secrets.
5. Define explicit `not_astrology`, `needs_profile`, `computed`, `degraded`, and `blocked` branches. Non-astrology conversation must not spend a calculation; incomplete birth data must not produce synthetic chart claims.

### Tests

- Contract tests prove career, relationship, wealth, and timing questions invoke `/api/consultation_workflow` exactly once before text is emitted.
- Follow-up reuse is allowed only for matching chart/configuration/version; differing birth data, reference date, ayanamsa, node mode, or required domain invalidates reuse.
- Model-mock tests prove a model cannot bypass a required invocation.
- Stream tests prove receipts contain no personal or secret fields.

## Phase 1: Enforce Route-Specific Skill Completeness

1. Create one versioned TypeScript schema for the commercial projection of the Python workflow response. Parse it in `frontend/src/mastra/index.ts`; reject malformed or incomplete results instead of passing untyped records to the model.
2. Build an executable route matrix from `SKILL.md`, strict-workflow contracts, and the technique registry. At minimum enforce:
   - career: D10 + A10 and functional benefic/malefic;
   - relationship: D9 + UL and functional benefic/malefic;
   - wealth: D2/D11 and functional benefic/malefic;
   - timing/event: Vimshottari + Narayana Dasha, required Dasha boundaries, transit status, and external-evidence status.
3. The API projection carries technique `used/not_used/blocked`, missing layers, conflict resolution, confidence boundary, and the raw-evidence identifiers required by the selected route.
4. Add a Python-to-TypeScript golden fixture for every route and every terminal status (`ready`, `degraded`, `blocked`). Fixtures must use public synthetic cases only.
5. Cross-check the frontend-reachable endpoint inventory against Python dispatch. Fail CI when a new user-reachable operation has no handler, no schema, or no capability contract.

### Tests

- Golden parity for route projection and error/status preservation.
- Negative tests delete each required layer and assert the commercial answer cannot make the corresponding claim.
- Endpoint reachability inventory test includes `/api/consultation_workflow`, daily guidance, synastry, and all birth-time routes.

## Phase 2: Truthful External-Oracle Degradation

1. Treat the current `fast_local_fallback` as a first-class execution state in the commercial response contract, not an incidental log value.
2. Map external layers independently: PyJHora/JHora comparison, jyotishganit, VedAstro official raw snapshot, parity status, and real-case calibration. Preserve license boundaries.
3. When a premium key or official snapshot is unavailable, retain local computation but force the exact affected conclusion to `degraded` or `blocked` according to the strict-workflow contract. Do not silently say an external check ran.
4. Add a configurable official-snapshot budget/timeout with a circuit state and sanitized telemetry. The fallback must be deterministic, bounded, and visible to audit metadata.
5. Add a deployment gate that runs the existing adapter diagnostics and a selected public-synthetic same-chart replay. It must report `unavailable`, `partial_verified`, and `mismatch` distinctly rather than failing open.

### Tests

- No-key, timeout, malformed-provider, parity-mismatch, and fully-available fixtures.
- Assertions that the language-model context never upgrades `partial_verified` to verified or hides a material blocked layer.
- License/attribution snapshot test for every enabled external adapter.

## Phase 3: Optimize Real Engine Cost And Reliability

1. Instrument only actual entrypoints (`consultation_workflow`, chart, synastry, daily guidance, high-rigor workflow) with sanitized elapsed-time spans: routing, ephemeris/chart, divisional charts, dasha, Shadbala/Ashtakavarga, external adapters, serialization.
2. Benchmark public synthetic charts by route/configuration on the production-equivalent 1-vCPU/2-GB budget. Establish p50/p95, response-size, timeout, and queue-depth budgets before caching or parallelization.
3. Memoize only immutable, configuration-keyed computation fragments. Use a bounded TTL/LRU keyed by a cryptographic digest of normalized input and computation settings; never cache raw profile data, user text, credentials, or final personalized prose.
4. Keep high-rigor/batch/external-heavy paths asynchronous when their measured p95 exceeds the interactive budget. Preserve existing job identity, polling, cancellation, and evidence-packet retrieval semantics.
5. Reduce model context to the route-required evidence projection. Full raw packets remain retrievable only through the authenticated/auditable path, avoiding token cost and accidental evidence loss in chat rendering.

### Tests

- Determinism before/after cache hit; ayanamsa/node-mode/reference-date changes must miss cache.
- Concurrent identical requests do not duplicate expensive work; cancellation never corrupts a shared result.
- Benchmark regression thresholds and response-shape snapshots.

## Phase 4: Wire Secondary Live Flows Into The Same Truth Contract

1. Daily guidance must carry reference date, transit source/configuration, local/external state, and a bounded claim scope; no generic model prose may replace chart-derived daily data.
2. Synastry must preserve both chart settings, Ashtakoot method/version, D9 evidence, relationship-route required layers, and non-comparability states.
3. Birth-time guidance/rectification remains evidence-collection and candidate-scoring only. It cannot present a candidate as a verified birth time until its configured evidence threshold and strict workflow state are met.
4. Use one commercial `AstrologyExecutionEnvelope` for the shared status/audit fields while retaining route-specific payloads. This is an adapter boundary, not a rewrite of engine formulas.

### Tests

- Daily date-boundary and fallback fixtures.
- Synastry settings mismatch/non-comparability fixtures.
- Rectification candidate confidence and no-premature-certainty fixtures.

## Phase 5: Commercial Capability Intake

When the owner approves a research-derived capability, add it only through a commercial intake manifest containing capability ID/version, approved interface, supplied source hash, license/attribution decision, input/output contract, privacy class, test fixture provenance, rollout flag, observability, and rollback path. The commercial adapter consumes that interface only; it does not import a research working tree.

## Execution Order

1. Reconcile local branch with upstream before editing runtime behavior.
2. Phase 0 deterministic invocation.
3. Phase 1 route-completeness schemas and golden contracts.
4. Phase 2 external-degradation truth handling.
5. Phase 3 measured engine performance/reliability.
6. Phase 4 secondary live flows.
7. Phase 5 only after an owner-approved capability handoff.

Each phase requires relevant Python + frontend tests, user-invocation acceptance, adapter diagnostics, production build, and `git diff --check`. Push/deploy needs separate owner authorization.
