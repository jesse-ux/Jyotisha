# Commercial Repository Optimization Plan

**Scope:** `jesse-ux/Jyotisha` commercial repository only. The research repository remains an external, owner-approved source of validated capability artifacts. No research source code, raw data, or internal validation chain is modified by this plan.

## Baseline And Evidence

- Local branch: `codex/optimize-runtime-ux`, based on `3d6d498`; upstream `main` is now `51decd5003df1a33f49e71d6469e5a0cd382e7dc`. Reconcile before implementation; do not overwrite local changes.
- Existing local change: lazy-load birth-time rectification. Largest first-page chunk measured `826,370 B -> 710,726 B` (about `115.6 KB` reduction).
- `npm test`: `264/264` pass. `npm run lint`: exit success, two existing `react-hooks/exhaustive-deps` warnings in `frontend/src/app/page.tsx` lines 1176 and 1192.
- Production smoke: `https://jyotisha.chat/` returns `200`, static cache hit, and `/api/health` returns environment/provider status plus internal API latency publicly.
- Official-registry dependency audit: 5 findings (3 low, 2 moderate), including direct `next`/transitive `postcss` and `@mastra/core`/AI SDK dependency paths. The configured `npmmirror` cannot provide npm security advisories; its audit endpoint returns `404`.
- Public evidence consulted: [Next.js lazy loading](https://nextjs.org/docs/app/guides/lazy-loading), [Next.js production checklist](https://nextjs.org/docs/app/guides/production-checklist), [Supabase SSR](https://supabase.com/docs/guides/auth/server-side/creating-a-client), and [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use).

## Acceptance Rules

- No research repository write, dependency, path, raw evidence, or secret enters the commercial repository without an explicit approved intake record.
- Preserve account, credits, cancellation, and existing business tests. Do not expose user identity, birth data, prompts, model keys, or Supabase service keys in logs, telemetry, responses, or build artifacts.
- A public liveness route may reveal only a coarse status. Dependency readiness and diagnostic detail must remain Docker-private or token-gated.
- Every performance claim needs before/after build evidence. Every dependency update needs audit output and full test/build evidence.

## Phase 0: Reconcile And Freeze Baseline

1. Run `git fetch origin main`, inspect `3d6d498..origin/main`, and rebase or manually port only the local lazy-load change after reviewing conflicts.
2. Record immutable baseline artifacts: `npm ci`, `npm test`, `npm run lint`, `npm run build`, official-registry `npm audit --omit=dev --registry=https://registry.npmjs.org`, route-size manifest, and production header/health samples.
3. Add a CI-independent script, `frontend/scripts/verify-production-baseline.mjs`, that emits sanitized JSON for test/build/audit/bundle-budget evidence. It must explicitly select `registry.npmjs.org` for audit.

**Tests:** existing test suite; build; `git diff --check`; baseline script fixture test.

## Phase 1: Supply Chain And Release Controls

1. Upgrade direct vulnerable dependencies to the newest compatible patched releases, regenerate only `frontend/package-lock.json`, and re-run the official audit. Do not accept the audit tool's suggested semver-major downgrade/upgrade blindly; inspect the resolved tree first.
2. Add `dependabot.yml` for GitHub Actions, root Python, `frontend`, and `jyotish-app`; group patch/minor updates by ecosystem while retaining PR review.
3. In CI, run official-registry production audit, frontend lint/tests/build, and a lockfile integrity check. Use GitHub Actions concurrency to cancel obsolete PR runs. Pin third-party actions to immutable commit SHAs after verifying publishers and versions.
4. Keep deployment gated on the same commit that passed CI. Add a release evidence artifact containing dependency audit summary, build identifier, and sanitized production smoke result.

**Tests:** audit reaches zero high/critical; dependency-specific regression tests; full frontend test/build; workflow syntax validation.

## Phase 2: Public Edge And API Hardening

1. Split health semantics:
   - `GET /api/health`: public liveness only, no environment names, provider presence, topology, or internal latency.
   - an internal-only diagnostic route or direct Docker healthcheck: detailed dependency checks, accessible only from the compose network or through a deployment-only token.
   - Add route tests proving detail cannot reach the public response.
2. Add Caddy edge headers: `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, clickjacking protection, and production HSTS. Design CSP in report-only mode first because Next.js/Supabase scripts and streaming require nonce/hash validation; promote only after browser and login-flow verification.
3. Map all mutating API routes to explicit authentication, schema validation, authorization, idempotency, timeout, and rate-limit behavior. Preserve the existing credit RPC as the billing authority; add a durable per-user guard only where the current credit lifecycle does not already prevent expensive model work.
4. Add request IDs and sanitized structured event fields (`route`, `status`, `latency_ms`, `model_id`, `credit_transition`, `error_class`). Explicitly prohibit prompt/profile/body logging.

**Tests:** public health redaction, internal health success in compose, unauthenticated/malformed/over-limit cases for every mutation route, streamed consultation cancellation, browser login/account/consult smoke.

## Phase 3: First-Use Performance And Frontend Maintainability

1. Keep the existing lazy-loaded rectification subtree and turn its measured saving into a regression budget. Add a bundle report that identifies first-page JS separately from deferred chunks; fail CI only on a deliberate, reviewed budget breach.
2. Defer heavy onboarding-only data, beginning with `china-locations`, until the location step opens. Preserve typed loading/error states and keyboard behavior.
3. Split `frontend/src/app/page.tsx` (2,643 lines) by stable product boundaries, not generic abstractions:
   - session/chat composer and streaming lifecycle;
   - onboarding/profile and birth-time flow;
   - chart library and synastry history;
   - account/model-selection orchestration.
   State ownership remains at the smallest shared parent; pure transformations move to tested `lib` modules.
4. Resolve the two exhaustive-deps warnings by proving the intended dependency model through tests, rather than silencing lint rules. Avoid adding `profile` wholesale if that would cause duplicate network calls; extract stable primitive dependencies or a memoized request key.
5. Validate desktop/mobile rendering, loading fallback, focus order, reduced-motion behavior, and long Chinese content after each split.

**Tests:** unit tests for extracted state transitions; existing source-contract tests updated only for behavior; Playwright flows for login, onboarding, guided rectification, cancel/retry, chat session switching, account dialogs; production bundle comparison.

## Phase 4: Commercial Capability Intake Boundary

1. Add `docs/commercial-capability-intake.md` plus a machine-readable `frontend/src/lib/capability-manifest.ts` only when a research capability is approved for commercial use.
2. Each intake row records: capability ID/version, permitted interface, source commit/hash supplied by the owner, license/attribution decision, accepted input/output schema, user-facing fallback, privacy classification, test fixture provenance, and rollback switch.
3. Commercial adapters call only the approved stable interface. They must not import a research checkout, scrape research artifacts, or claim research-level validation beyond the supplied manifest.
4. Gate every intake behind contract tests, a staged feature flag, production observability, and an explicit rollback procedure.

**Tests:** manifest schema validation; adapter contract fixtures; feature-flag off fallback; rollback integration test.

## Execution Order

1. Phase 0 reconcile/baseline.
2. Phase 1 dependencies and CI controls.
3. Phase 2 health/edge/API hardening.
4. Phase 3 performance decomposition and browser verification.
5. Phase 4 only when an owner-approved research capability arrives.

Each phase ends with `git diff --check`, full relevant tests, production build, and an evidence note. Deployment/push remains separate owner authorization.
