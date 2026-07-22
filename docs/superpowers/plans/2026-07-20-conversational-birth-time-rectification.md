# Conversational Birth-Time Rectification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace onboarding’s generic choice questionnaire with a homepage-card conversational rectification flow that preserves rich chart-grounded explanations while recording evidence, billing, candidate revisions, and final confirmation in one durable account-level case.

**Architecture:** Keep ordinary chat sessions as presentation only. Add a `conversational-evidence-v3` case protocol, an idempotent server orchestrator, and a dual response containing both a user-facing narrative and a machine-validated technical receipt. Reuse existing deterministic scan/event-scoring capabilities, but do not reuse the dynamic-choice UI or its generic question-generation policy as the new user journey.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript 5, Zod 3, Supabase/PostgreSQL RPCs and RLS, Mastra Agent streaming, Node’s test runner with `tsx`, Python `pytest`, Docker Compose, Caddy.

## Global Constraints

- Initialization collects declared birth facts only and never blocks entry to the homepage on rectification completion.
- `birth_time_rectification` is the sole visible entrypoint for start, resume, and re-rectification.
- Unrectified users may continue with an unverified concrete time for the current chat, or rectify first; never invent a minute for period-only or unknown input.
- The first and final rectification messages remain rich, chart-grounded narratives; intermediate turns are focused updates, not generic range questionnaires.
- Future windows may be shown as context but never scored as historical evidence.
- The model never chooses or writes an active birth minute; only an atomic server confirmation RPC may update `profiles.active_birth_time`.
- Re-rectification preserves the previous active time until confirmation succeeds.
- One fixed server-configured fee covers one case; start failures refund, resume/retry do not recharge, and pre-launch unfinished legacy cases receive one migration-waived continuation.
- Chat deletion never deletes rectification cases; new chat creation never resets them.
- All mutations require owner identity, `turnVersion`, and an idempotent `actionId`.
- Do not log or fixture access tokens, refresh tokens, cookies, emails, user UUIDs, or real birth data.
- Use synthetic profile and event fixtures in every test.

---

## File Structure

### Existing files to modify

- `frontend/src/app/page.tsx` — page-level profile state, soft consent, card routing, saved ordinary question, and chat-session integration.
- `frontend/src/lib/birth-time-client-transport.ts` — stable JSON/non-JSON and WebKit error handling.
- `frontend/src/lib/birth-time-journey-request.ts` — temporary v2 dynamic candidate confirmation command.
- `frontend/src/hooks/use-birth-time-guided-journey.ts` — protocol-correct v2 confirmation during migration.
- `frontend/src/app/api/birth-time-journey/route.ts` — route the temporary dynamic confirmation action.
- `frontend/src/lib/birth-time-journey-service.ts` — expose the temporary dynamic confirmation method.
- `frontend/src/app/api/consult/route.ts` — ordinary consultation consent handoff only; rectification no longer runs as `direct_chart` chat.
- `frontend/src/lib/birth-time-intake-model.ts` — distinguish declared completeness from chart-ready status.
- `frontend/src/components/birth-time-intake.tsx` — keep declared fields editable without forcing rectification.
- `deploy/docker-compose.server.yml`, `deploy/Caddyfile`, `.github/workflows/deploy-production.yml` — ready-only web routing and deployment verification.

### New bounded modules

- `frontend/src/lib/conversational-rectification/contracts.ts` — public commands, responses, and Zod schemas.
- `frontend/src/lib/conversational-rectification/errors.ts` — stable domain error codes and Chinese recovery copy.
- `frontend/src/lib/conversational-rectification/store.ts` — Supabase case/turn/evidence/RPC adapter.
- `frontend/src/lib/conversational-rectification/billing.ts` — fixed-fee reserve/complete/release adapter.
- `frontend/src/lib/conversational-rectification/technical-packet.ts` — deterministic candidate and sensitive-layer packet builder.
- `frontend/src/lib/conversational-rectification/narrative-agent.ts` — grounded narrative generation and validation.
- `frontend/src/lib/conversational-rectification/evidence-extractor.ts` — raw-text event normalization without scoring ambiguous events.
- `frontend/src/lib/conversational-rectification/orchestrator.ts` — start/resume/answer/pause/abandon/confirm application service.
- `frontend/src/lib/conversational-rectification/client.ts` — browser API client with replay-safe actions.
- `frontend/src/lib/conversational-rectification/legacy-import.ts` — read-only v1/v2 import into one waived v3 revision.
- `frontend/src/app/api/birth-time-conversation/route.ts` — authenticated discriminated-command API.
- `frontend/src/hooks/use-conversational-rectification.ts` — UI controller for durable case turns.
- `frontend/src/components/conversational-birth-time-rectification.tsx` — narrative, event-domain actions, free input, evidence recap, and final confirmation.
- `frontend/src/components/unverified-birth-time-choice.tsx` — soft choice between unverified consultation and rectification-first.

### New migrations

- `frontend/supabase/migrations/20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql`
- `frontend/supabase/migrations/20260720010000_conversational_rectification_schema.sql`
- `frontend/supabase/migrations/20260720020000_conversational_rectification_billing.sql`
- `frontend/supabase/migrations/20260720030000_conversational_rectification_transitions.sql`

---

### Task 1: Close chat deletion and browser transport failures

**Files:**
- Create: `frontend/supabase/migrations/20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql`
- Create: `frontend/tests/chat-session-delete-contract.test.ts`
- Create: `frontend/tests/birth-time-client-transport.test.ts`
- Modify: `frontend/src/lib/birth-time-client-transport.ts`

**Interfaces:**
- Produces: owner-only `DELETE` support for `chat_sessions` and `postJson()` behavior that converts non-JSON error responses into `payload: null` for both native `SyntaxError` and WebKit `DOMException` named `SyntaxError`.
- Consumes: existing `postJson(JsonPostInput): Promise<JsonPostResult>`.

- [ ] **Step 1: Add failing owner-delete migration contract**

```ts
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const sql = readFileSync(new URL(
  "../supabase/migrations/20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql",
  import.meta.url,
), "utf8");

test("chat sessions expose owner-only delete", () => {
  assert.match(sql, /create policy chat_sessions_delete_own[\s\S]*for delete[\s\S]*auth\.uid\(\).*user_id/i);
  assert.match(sql, /grant delete on table public\.chat_sessions to authenticated/i);
});
```

- [ ] **Step 2: Add failing WebKit/non-JSON transport tests**

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { postJson } from "../src/lib/birth-time-client-transport.ts";

test("non-json 502 returns a null payload instead of leaking WebKit syntax text", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => new Response("bad gateway", { status: 502 });
  try {
    const result = await postJson({ url: "/x", body: "{}", retryLostResponse: false });
    assert.equal(result.response.status, 502);
    assert.equal(result.payload, null);
  } finally { globalThis.fetch = original; }
});

test("DOMException SyntaxError is classified as a lost response", async () => {
  const original = globalThis.fetch;
  let attempts = 0;
  globalThis.fetch = async () => {
    attempts += 1;
    if (attempts === 1) throw new DOMException("pattern", "SyntaxError");
    return Response.json({ ok: true });
  };
  try {
    const result = await postJson({ url: "/x", body: "{}", retryLostResponse: true });
    assert.deepEqual(result.payload, { ok: true });
  } finally { globalThis.fetch = original; }
});
```

- [ ] **Step 3: Run the focused tests and verify failure**

Run:

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test \
  frontend/tests/chat-session-delete-contract.test.ts \
  frontend/tests/birth-time-client-transport.test.ts
```

Expected: FAIL because the migration is absent and `DOMException("SyntaxError")` is not classified.

- [ ] **Step 4: Add the delete policy and robust syntax classifier**

Append this exact owner-delete section before the migration’s later dynamic-confirmation section:

```sql
begin;
drop policy if exists chat_sessions_delete_own on public.chat_sessions;
create policy chat_sessions_delete_own
  on public.chat_sessions for delete to authenticated
  using ((select auth.uid()) = user_id);
grant delete on table public.chat_sessions to authenticated;
commit;
```

Replace the transport classifier with:

```ts
function isJsonSyntaxError(error: unknown): boolean {
  return error instanceof SyntaxError
    || (error instanceof DOMException && error.name === "SyntaxError");
}

function isLostResponse(error: unknown, signal?: AbortSignal): boolean {
  return !isAbort(error, signal)
    && (error instanceof TypeError || isJsonSyntaxError(error));
}
```

In `postOnce`, return `{ response, payload: null }` for any non-OK response whose JSON parsing throws `isJsonSyntaxError`, without exposing `error.message`.

- [ ] **Step 5: Run focused tests**

Run the Step 3 command. Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/birth-time-client-transport.ts \
  frontend/tests/birth-time-client-transport.test.ts \
  frontend/tests/chat-session-delete-contract.test.ts \
  frontend/supabase/migrations/20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql
git commit -m "fix: close chat deletion and transport errors"
```

### Task 2: Make dynamic-v2 candidate confirmation protocol-correct

**Files:**
- Modify: `frontend/supabase/migrations/20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql`
- Create: `frontend/src/lib/birth-time-dynamic-candidate-confirmation.ts`
- Create: `frontend/tests/birth-time-dynamic-candidate-confirmation.test.ts`
- Modify: `frontend/src/lib/birth-time-journey-request.ts`
- Modify: `frontend/src/lib/birth-time-journey-service.ts`
- Modify: `frontend/src/app/api/birth-time-journey/route.ts`
- Modify: `frontend/src/hooks/use-birth-time-guided-journey.ts`
- Modify: `frontend/tests/birth-time-agent-flow-e2e.test.ts`

**Interfaces:**
- Produces: `BirthTimeJourneyService.confirmDynamicCandidate(input: DynamicCandidateConfirmationCommand): Promise<DynamicVersionedJourneyResponse>` and command `type: "confirm_dynamic_candidate"`.
- Consumes: `DynamicStoredRectificationCase`, current `request_candidate_confirmation`, candidate `resultId`, representative `time`, `actionId`, and `turnVersion`.

- [ ] **Step 1: Add failing service and end-to-end tests**

```ts
test("dynamic confirmation atomically reaches ready", async () => {
  const current = highConfidenceDynamicCase();
  const service = createBirthTimeJourneyService(memoryPorts(current));
  const result = await service.confirmDynamicCandidate({
    userId: current.userId,
    caseId: current.id,
    actionId: "a9890e09-d535-46f0-9a36-86017515a5a1",
    expectedVersion: current.dynamicTurnState.turnVersion,
    resultId: current.candidateResult!.resultId,
    time: current.candidateResult!.winningSegment!.representativeTime,
  });
  assert.equal(result.nextAction.kind, "ready");
  assert.equal(result.snapshot.activeTime, "17:15");
});
```

Extend the existing agent-flow E2E test to call the confirmation command after `request_candidate_confirmation`, then resume and assert both responses remain `ready` with the same active time.

- [ ] **Step 2: Run the tests and verify failure**

Run:

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test \
  frontend/tests/birth-time-dynamic-candidate-confirmation.test.ts \
  frontend/tests/birth-time-agent-flow-e2e.test.ts
```

Expected: FAIL because no dynamic confirmation method or RPC exists.

- [ ] **Step 3: Add the public request and service transition**

Add this strict request variant:

```ts
z.object({
  type: z.literal("confirm_dynamic_candidate"),
  caseId: z.string().uuid(),
  actionId: z.string().uuid(),
  turnVersion: z.number().int().nonnegative(),
  resultId: z.string().uuid(),
  time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
}).strict()
```

Implement `confirmDynamicCandidate` to reject non-v2 cases, non-confirming actions, stale versions, result mismatches, non-representative times, or `canConfirmCandidate !== true`; construct `nextAction: { kind: "ready", activeTime: input.time }` and delegate persistence to the new store RPC.

- [ ] **Step 4: Add an atomic dynamic confirmation RPC**

Add `public.confirm_birth_time_dynamic_candidate(uuid, uuid, uuid, time, uuid, bigint, jsonb, jsonb)` to the migration. It must lock the owned case, require `journey_protocol = 'dynamic-choice-v2'`, replay an existing action ID, require the exact expected version/result/time/current action, update case status/snapshot/turn state/receipt, then update `profiles.active_birth_time`, `birth_time_status`, and `rectification_case_id` in the same transaction. Revoke public/anon/authenticated execution and grant only `service_role`.

- [ ] **Step 5: Route and branch the client controller**

In the API switch, add:

```ts
case "confirm_dynamic_candidate":
  return responseWithJourneyMetric(service.confirmDynamicCandidate({
    userId: user.id,
    caseId: parsed.data.caseId,
    actionId: parsed.data.actionId,
    expectedVersion: parsed.data.turnVersion,
    resultId: parsed.data.resultId,
    time: parsed.data.time,
  }), "turn_advanced");
```

In `use-birth-time-guided-journey.ts`, branch `confirmCandidate`: v2 sends `confirm_dynamic_candidate`; legacy continues sending `confirm_guided_candidate`.

- [ ] **Step 6: Run focused and legacy-isolation tests**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test \
  frontend/tests/birth-time-dynamic-candidate-confirmation.test.ts \
  frontend/tests/birth-time-agent-flow-e2e.test.ts \
  frontend/tests/birth-time-journey-legacy-isolation.test.ts
```

Expected: all PASS; legacy mutation rejection remains intact.

- [ ] **Step 7: Commit**

```bash
git add frontend/supabase/migrations/20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql \
  frontend/src/lib/birth-time-dynamic-candidate-confirmation.ts \
  frontend/src/lib/birth-time-journey-request.ts \
  frontend/src/lib/birth-time-journey-service.ts \
  frontend/src/app/api/birth-time-journey/route.ts \
  frontend/src/hooks/use-birth-time-guided-journey.ts \
  frontend/tests/birth-time-dynamic-candidate-confirmation.test.ts \
  frontend/tests/birth-time-agent-flow-e2e.test.ts
git commit -m "fix: confirm dynamic birth-time candidates"
```

### Task 3: Keep production traffic on a ready web container

**Files:**
- Modify: `deploy/docker-compose.server.yml`
- Modify: `deploy/Caddyfile`
- Modify: `.github/workflows/deploy-production.yml`
- Modify: `frontend/tests/health-deployment.test.ts`

**Interfaces:**
- Produces: a web healthcheck at `/api/health`, Caddy retry behavior for short upstream replacement windows, and deployment verification pinned to the tested SHA.

- [ ] **Step 1: Extend failing deployment contract tests**

Add assertions for a `web` healthcheck, `caddy.depends_on.web.condition: service_healthy`, Caddy `lb_try_duration`, and verification that `/api/health` returns the deployed SHA.

- [ ] **Step 2: Run and verify failure**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/health-deployment.test.ts
```

Expected: FAIL on the missing ready-only Caddy dependency/retry and SHA probe.

- [ ] **Step 3: Add readiness and bounded upstream retry**

Add to `web`:

```yaml
healthcheck:
  test: ["CMD", "node", "-e", "fetch('http://127.0.0.1:3000/api/health').then(r=>{if(!r.ok)process.exit(1)})"]
  interval: 30s
  timeout: 5s
  retries: 5
  start_period: 30s
  start_interval: 1s
```

Make Caddy depend on healthy web and configure:

```caddy
reverse_proxy web:3000 {
    lb_try_duration 10s
    lb_try_interval 250ms
}
```

Update verification to parse `/api/health` and require `deployment.gitCommit == DEPLOY_GIT_SHA` before success.

- [ ] **Step 4: Run deployment tests and config validation**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/health-deployment.test.ts
docker compose --env-file .env.example -f deploy/docker-compose.server.yml config --quiet
```

Expected: tests PASS and compose config exits 0. If `.env.example` lacks required interpolation values, pass non-secret dummy values inline rather than reading production secrets.

- [ ] **Step 5: Commit**

```bash
git add deploy/docker-compose.server.yml deploy/Caddyfile \
  .github/workflows/deploy-production.yml frontend/tests/health-deployment.test.ts
git commit -m "fix: keep deployment traffic on ready web"
```

### Task 4: Define the v3 public contract and domain errors

**Files:**
- Create: `frontend/src/lib/conversational-rectification/contracts.ts`
- Create: `frontend/src/lib/conversational-rectification/errors.ts`
- Create: `frontend/tests/conversational-rectification-contracts.test.ts`

**Interfaces:**
- Produces: `conversationalRectificationCommandSchema`, `conversationalRectificationTurnSchema`, `ConversationalRectificationCommand`, `ConversationalRectificationTurn`, and `ConversationalRectificationError`.

- [ ] **Step 1: Write failing schema tests**

Test exact strict commands: `start`, `resume`, `answer`, `pause`, `abandon`, `confirm`; require UUID `actionId`, nonnegative `turnVersion` after start, bounded answer text, strict `HH:mm`, and reject client-supplied candidate scores/technical receipts.

- [ ] **Step 2: Run and verify failure**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/conversational-rectification-contracts.test.ts
```

Expected: FAIL because the module is absent.

- [ ] **Step 3: Implement the strict contract**

Define the response around this exact public shape:

```ts
export const conversationalRectificationTurnSchema = z.object({
  caseId: z.string().uuid(),
  journeyProtocol: z.literal("conversational-evidence-v3"),
  status: z.enum(["active", "paused", "confirming", "completed", "abandoned"]),
  turnVersion: z.number().int().nonnegative(),
  narrative: z.string().trim().min(1).max(12_000),
  candidate: z.object({
    status: z.enum(["declared", "pending_validation", "ready_for_confirmation", "confirmed"]),
    representativeTime: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/).nullable(),
    rangeStart: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/).nullable(),
    rangeEnd: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/).nullable(),
  }).strict(),
  technicalReceipt: z.object({
    calculationVersion: z.string().trim().min(1).max(80),
    stableLayers: z.array(z.string().trim().min(1).max(80)).max(20),
    sensitiveLayers: z.array(z.string().trim().min(1).max(80)).max(20),
    candidateDifferenceRefs: z.array(z.string().trim().min(1).max(120)).max(40),
  }).strict(),
  evidenceRequest: z.object({
    domains: z.array(z.enum(["career", "education", "relocation", "relationship", "family", "other"])).min(2).max(4),
    datePrecision: z.enum(["month_preferred", "year_accepted"]),
    freeTextAllowed: z.literal(true),
  }).strict().nullable(),
  evidenceRecap: z.array(z.object({ id: z.string().uuid(), summary: z.string(), dateLabel: z.string() }).strict()).max(20),
  actions: z.array(z.enum(["answer", "pause", "abandon", "confirm", "continue_original_question"])).max(5),
  pendingConsultationQuestion: z.string().max(500).nullable(),
}).strict();
```

Map internal error codes to stable Chinese copy in `errors.ts`; never pass raw browser, SQL, or model error messages to the client.

- [ ] **Step 4: Run tests and commit**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/conversational-rectification-contracts.test.ts
git add frontend/src/lib/conversational-rectification/contracts.ts \
  frontend/src/lib/conversational-rectification/errors.ts \
  frontend/tests/conversational-rectification-contracts.test.ts
git commit -m "feat: define conversational rectification contract"
```

Expected: tests PASS and one focused contract commit is created.

### Task 5: Add v3 persistence, fixed-fee billing, and atomic transitions

**Files:**
- Create: `frontend/supabase/migrations/20260720010000_conversational_rectification_schema.sql`
- Create: `frontend/supabase/migrations/20260720020000_conversational_rectification_billing.sql`
- Create: `frontend/supabase/migrations/20260720030000_conversational_rectification_transitions.sql`
- Create: `tests/test_conversational_rectification_contract.py`
- Create: `frontend/src/lib/conversational-rectification/store.ts`
- Create: `frontend/src/lib/conversational-rectification/billing.ts`
- Create: `frontend/tests/conversational-rectification-store.test.ts`

**Interfaces:**
- Produces: `ConversationalRectificationStore` with `createCaseWithFirstTurn`, `loadCase`, `saveTurn`, `pause`, `abandon`, `confirm`, and `importLegacy`; billing methods `reserve`, `complete`, `release`.

- [ ] **Step 1: Write failing SQL and store contract tests**

Assert protocol constraint includes `conversational-evidence-v3`; new case/turn/evidence/billing tables are service-role-only; all mutation RPCs lock owned rows, replay action receipts, check versions, and never expose authenticated table grants. Assert confirm updates case and profile in one RPC.

- [ ] **Step 2: Run and verify failure**

```bash
.venv/bin/python -m pytest tests/test_conversational_rectification_contract.py -q
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/conversational-rectification-store.test.ts
```

Expected: FAIL because migrations/store are absent.

- [ ] **Step 3: Create bounded tables**

Create:

- `birth_time_rectification_turns` keyed by `(case_id, turn_version)` with bounded public narrative and JSON technical receipt;
- `birth_time_rectification_event_evidence` with raw text, normalized domain/date/precision/status, and source turn;
- `birth_time_rectification_action_receipts` keyed by `(case_id, action_id)`;
- `birth_time_rectification_billing` keyed by `case_id`, with `reserved|charged|released|migration_waived`;
- case columns `revision_of_case_id`, `imported_from_case_id`, `baseline_active_time`, `pending_consultation_question`, and v3 protocol support.

Revoke anon/authenticated access and grant only service role. Store only user-visible narrative in the public turn projection; keep internal candidate weights private.

- [ ] **Step 4: Add configurable fixed-fee RPCs**

Use a server-supplied `p_price` validated as a positive bounded integer, advisory-lock `(user, actionId)`, reserve exact credits once, complete without another debit, release exactly once, and create `migration_waived` without changing credits. Return `{ success, credits, billing_state, error_code }`.

- [ ] **Step 5: Add versioned save/import/confirm RPCs**

`create_conversational_rectification_case` must atomically create case + first turn + action receipt, then allow billing completion. `save_conversational_rectification_turn` saves raw evidence and the new turn in one transaction. `confirm_conversational_rectification_candidate` verifies owner/version/result/time/technical version, writes confirmation receipt, updates `profiles.active_birth_time`, closes the case, and returns the pending ordinary question.

- [ ] **Step 6: Implement the typed store adapters**

The adapter must translate Supabase errors into `ConversationalRectificationError` codes: `case_not_found`, `stale_turn`, `action_conflict`, `candidate_changed`, `billing_failed`, `store_unavailable`. It must never expose `error.message` to clients.

- [ ] **Step 7: Run tests and commit**

Run the Step 2 commands. Expected: all PASS.

```bash
git add frontend/supabase/migrations/20260720010000_conversational_rectification_schema.sql \
  frontend/supabase/migrations/20260720020000_conversational_rectification_billing.sql \
  frontend/supabase/migrations/20260720030000_conversational_rectification_transitions.sql \
  frontend/src/lib/conversational-rectification/store.ts \
  frontend/src/lib/conversational-rectification/billing.ts \
  frontend/tests/conversational-rectification-store.test.ts \
  tests/test_conversational_rectification_contract.py
git commit -m "feat: persist and bill conversational rectification"
```

### Task 6: Build grounded technical packets, evidence extraction, and rich narratives

**Files:**
- Create: `frontend/src/lib/conversational-rectification/technical-packet.ts`
- Create: `frontend/src/lib/conversational-rectification/evidence-extractor.ts`
- Create: `frontend/src/lib/conversational-rectification/narrative-agent.ts`
- Create: `frontend/tests/conversational-technical-packet.test.ts`
- Create: `frontend/tests/conversational-evidence-extractor.test.ts`
- Create: `frontend/tests/conversational-narrative-agent.test.ts`

**Interfaces:**
- Produces: `buildRectificationTechnicalPacket`, `extractLifeEventEvidence`, `generateRectificationNarrative`, and `validateNarrativeAgainstPacket`.
- Consumes: existing Jyotish scan/event-score engine and server-computed consultation workflow; never consumes client-authored technical facts.

- [ ] **Step 1: Add failing synthetic quality tests**

Use a synthetic profile fixture. Assert the first-turn packet identifies stable/sensitive layers and at least two evidence domains; clear text such as `2021年7月毕业并去外地工作` extracts month precision and two event facts; vague text remains `needs_clarification`; future dates are marked non-scoreable.

- [ ] **Step 2: Add a rich-response regression test**

Assert first-turn output includes candidate status, use boundary, stable/sensitive evidence, why the selected domains discriminate, and a request for past event month/year. Reject a response consisting only of generic range choices. Use semantic fields and regex assertions, not a byte-for-byte model snapshot.

- [ ] **Step 3: Run and verify failure**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test \
  frontend/tests/conversational-technical-packet.test.ts \
  frontend/tests/conversational-evidence-extractor.test.ts \
  frontend/tests/conversational-narrative-agent.test.ts
```

Expected: FAIL because the three modules are absent.

- [ ] **Step 4: Implement deterministic packet construction**

Return a private packet containing candidate range/model references, D1 stability, boundary distance, supported sensitive layers, scored historical evidence, suggested domains, calculation version, and future windows tagged `scoreable: false`. Strip candidate weights and partition IDs before public projection.

- [ ] **Step 5: Implement evidence extraction and correction semantics**

Always preserve `rawText`. Return `clear` only when event summary and at least year are present; return `needs_clarification` without scoring otherwise. Split multi-event sentences into separate evidence rows linked to the same source turn. Never infer a missing month or fabricate a date.

- [ ] **Step 6: Implement grounded narrative generation and validation**

Generate first/intermediate/final prompts from the private technical packet. Parse structured model output, then validate every mentioned representative time/layer/reference against the packet. On mismatch, retry expression once with the same packet; on a second failure, return a deterministic Chinese fallback and do not advance evidence scoring.

- [ ] **Step 7: Run tests and commit**

Run the Step 3 command. Expected: all PASS.

```bash
git add frontend/src/lib/conversational-rectification/technical-packet.ts \
  frontend/src/lib/conversational-rectification/evidence-extractor.ts \
  frontend/src/lib/conversational-rectification/narrative-agent.ts \
  frontend/tests/conversational-technical-packet.test.ts \
  frontend/tests/conversational-evidence-extractor.test.ts \
  frontend/tests/conversational-narrative-agent.test.ts
git commit -m "feat: generate grounded rectification turns"
```

### Task 7: Implement the v3 orchestrator and authenticated API

**Files:**
- Create: `frontend/src/lib/conversational-rectification/orchestrator.ts`
- Create: `frontend/src/app/api/birth-time-conversation/route.ts`
- Create: `frontend/tests/conversational-rectification-orchestrator.test.ts`
- Create: `frontend/tests/conversational-rectification-route.test.ts`

**Interfaces:**
- Produces: `createConversationalRectificationService(ports)` with `start`, `resume`, `answer`, `pause`, `abandon`, `confirm`; `ports.rectificationPriceCredits` is server-owned; authenticated POST route accepting `ConversationalRectificationCommand` without a client price field.

- [ ] **Step 1: Add failing service state-machine tests**

Cover: first-turn reserve/compute/save/charge order; failure releases; clear evidence rescoring; ambiguous evidence clarification; unmatched/free direction change; pause/resume; stale rejection; idempotent replay; re-rectification baseline preservation; confirm returning the saved ordinary question.

- [ ] **Step 2: Add failing route boundary tests**

Assert authentication precedes body parsing; invalid commands return 400 before billing; domain conflicts return stable 409; service unavailability returns stable 503 Chinese copy; raw SQL/model/browser messages never appear.

- [ ] **Step 3: Run and verify failure**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test \
  frontend/tests/conversational-rectification-orchestrator.test.ts \
  frontend/tests/conversational-rectification-route.test.ts
```

Expected: FAIL because service and route are absent.

- [ ] **Step 4: Implement orchestration order**

`start`: validate declared profile → read `ports.rectificationPriceCredits` → reserve/waive → build packet → generate/validate narrative → atomically create case+turn → complete charge; on failure release. Reject any unknown client fields, so a caller cannot choose the price. `answer`: load/version-check → save raw text → extract → clarify or score → build packet → narrate → atomically save turn. `confirm`: delegate only to atomic RPC.

- [ ] **Step 5: Implement authenticated route**

Create server and admin Supabase clients after authentication. Parse strict commands, build ports, call one service method, and return the public response. Convert only known domain errors; log request/action/case correlation IDs without personal data.

- [ ] **Step 6: Run tests and commit**

Run Step 3. Expected: all PASS.

```bash
git add frontend/src/lib/conversational-rectification/orchestrator.ts \
  frontend/src/app/api/birth-time-conversation/route.ts \
  frontend/tests/conversational-rectification-orchestrator.test.ts \
  frontend/tests/conversational-rectification-route.test.ts
git commit -m "feat: orchestrate conversational rectification"
```

### Task 8: Add the browser client, controller, and rich conversation surface

**Files:**
- Create: `frontend/src/lib/conversational-rectification/client.ts`
- Create: `frontend/src/hooks/use-conversational-rectification.ts`
- Create: `frontend/src/components/conversational-birth-time-rectification.tsx`
- Create: `frontend/tests/conversational-rectification-client.test.ts`
- Create: `frontend/tests/conversational-rectification-controller.test.ts`
- Create: `frontend/tests/conversational-rectification-component.test.ts`
- Modify: `frontend/src/app/globals.css`

**Interfaces:**
- Produces: `sendConversationalRectificationCommand`, `useConversationalRectification`, and `ConversationalBirthTimeRectification`.

- [ ] **Step 1: Write failing client/controller/component contract tests**

Assert stable action IDs survive lost-response retries, one mutation at a time, stale turns reload, typed text restores on failure, narrative renders before domain buttons, free text remains available, evidence recap is correctable, and final confirm is explicit.

- [ ] **Step 2: Run and verify failure**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test \
  frontend/tests/conversational-rectification-client.test.ts \
  frontend/tests/conversational-rectification-controller.test.ts \
  frontend/tests/conversational-rectification-component.test.ts
```

Expected: FAIL because modules/components are absent.

- [ ] **Step 3: Implement client and controller**

Use `postJson` with replay enabled for all action-ID commands. Keep a stable identity registry keyed by case/version/operation/payload. On 409 stale turn, call `resume`; on 502/non-JSON failure, show stable Chinese copy and preserve input.

- [ ] **Step 4: Implement the accessible conversation surface**

Render Markdown narrative, 2–4 domain buttons, a free-text composer, evidence recap/edit affordance, pause/abandon controls, and candidate confirmation. Buttons are at least 44px, pending state locks duplicate actions, and mobile width is verified at 390px. Do not render the old broad-year choice component in v3.

- [ ] **Step 5: Run tests, lint focused files, and commit**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test \
  frontend/tests/conversational-rectification-client.test.ts \
  frontend/tests/conversational-rectification-controller.test.ts \
  frontend/tests/conversational-rectification-component.test.ts
cd frontend && npm run lint -- \
  src/lib/conversational-rectification/client.ts \
  src/hooks/use-conversational-rectification.ts \
  src/components/conversational-birth-time-rectification.tsx
```

Expected: tests and lint PASS.

```bash
git add frontend/src/lib/conversational-rectification/client.ts \
  frontend/src/hooks/use-conversational-rectification.ts \
  frontend/src/components/conversational-birth-time-rectification.tsx \
  frontend/src/app/globals.css frontend/tests/conversational-rectification-*.test.ts
git commit -m "feat: render conversational rectification"
```

### Task 9: Replace onboarding hard gating with homepage soft choice and card state

**Files:**
- Create: `frontend/src/components/unverified-birth-time-choice.tsx`
- Create: `frontend/src/lib/birth-time-consultation-consent.ts`
- Create: `frontend/tests/birth-time-consultation-consent.test.ts`
- Modify: `frontend/src/app/api/account/route.ts`
- Create: `frontend/tests/account-api.test.ts`
- Modify: `frontend/src/lib/birth-time-intake-model.ts`
- Modify: `frontend/src/components/birth-time-intake.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/tests/birth-time-intake.test.ts`
- Modify: `frontend/tests/consultation-entrypoint.test.ts`

**Interfaces:**
- Produces: `isDeclaredBirthProfileComplete`, `requiresBirthTimeConsent`, per-chat consent state, server-provided `rectificationPriceCredits`, card action `start|resume|revise`, and homepage rendering of v3 surface.

- [ ] **Step 1: Write failing business-flow tests**

Assert declared date/source/place completes onboarding even when `active_birth_time` is null; unverified concrete time triggers soft choice; period-only/unknown cannot select “use unverified minute”; consent is scoped to one chat; new chat resets consent but not case; account API returns the positive server-configured fixed price; card resolves start/resume/revise from account case state.

- [ ] **Step 2: Run and verify failure**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test \
  frontend/tests/birth-time-consultation-consent.test.ts \
  frontend/tests/birth-time-intake.test.ts \
  frontend/tests/consultation-entrypoint.test.ts \
  frontend/tests/account-api.test.ts
```

Expected: FAIL because completeness still requires candidate/confirmed active time and the card only drafts a normal consultation.

- [ ] **Step 3: Separate declared completeness from chart readiness**

Keep `isBirthTimeReadyForConsultation` for exact chart use, add `isDeclaredBirthProfileComplete` for onboarding, and make `missingProfileStep` stop after name/birth/place. Do not call `requestBirthTimeAssessment()` from `saveOnboardingPlace` or normal profile save.

- [ ] **Step 4: Add per-chat consent and card routing**

Read `RECTIFICATION_PRICE_CREDITS` on the server, validate it as an integer from 1 through 100, and return it from `/api/account` as `rectificationPriceCredits`; use a checked default of `1` only when the variable is absent. Before ordinary `/api/consult`, if time is unverified and the session lacks consent, show `UnverifiedBirthTimeChoice`. Choosing unverified use sets consent on that session only. Choosing rectify stores the question and starts/resumes v3. Card click must no longer send `birth_time_rectification` through ordinary `/api/consult`; it opens the v3 controller using account case state and displays the returned fixed price before the start action.

- [ ] **Step 5: Run tests and commit**

Run Step 2. Expected: all PASS.

```bash
git add frontend/src/components/unverified-birth-time-choice.tsx \
  frontend/src/lib/birth-time-consultation-consent.ts \
  frontend/src/app/api/account/route.ts \
  frontend/src/lib/birth-time-intake-model.ts \
  frontend/src/components/birth-time-intake.tsx frontend/src/app/page.tsx \
  frontend/tests/birth-time-consultation-consent.test.ts \
  frontend/tests/birth-time-intake.test.ts frontend/tests/consultation-entrypoint.test.ts \
  frontend/tests/account-api.test.ts
git commit -m "feat: make birth-time rectification a soft homepage flow"
```

### Task 10: Preserve and resume the original consultation question

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/api/consult/route.ts`
- Create: `frontend/tests/rectification-question-handoff.test.ts`

**Interfaces:**
- Consumes: v3 `pendingConsultationQuestion` and action `continue_original_question`.
- Produces: explicit post-confirmation continuation into ordinary billing with the new active time.

- [ ] **Step 1: Add failing handoff tests**

Assert choosing rectify-first does not call `/api/consult` or debit ordinary credits; pause preserves the question; successful confirmation returns it; only an explicit continue action calls ordinary consult and uses the confirmed profile time; cancel restores the question without charge.

- [ ] **Step 2: Run and verify failure**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/rectification-question-handoff.test.ts
```

Expected: FAIL because ordinary questions are not durably handed through rectification.

- [ ] **Step 3: Implement the handoff**

Store the original visible question in the case start command. On confirmed response, render `使用新确认时间继续回答原问题`. Only that click calls existing `send(question, theme)` without the rectification entrypoint; normal billing reserve/complete/cancel remains unchanged.

- [ ] **Step 4: Run tests and commit**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/rectification-question-handoff.test.ts
git add frontend/src/app/page.tsx frontend/src/app/api/consult/route.ts \
  frontend/tests/rectification-question-handoff.test.ts
git commit -m "feat: resume questions after birth-time confirmation"
```

### Task 11: Import unfinished legacy cases without restoring generic questions

**Files:**
- Create: `frontend/src/lib/conversational-rectification/legacy-import.ts`
- Create: `frontend/tests/conversational-legacy-import.test.ts`
- Modify: `frontend/src/lib/conversational-rectification/orchestrator.ts`
- Modify: `frontend/src/lib/conversational-rectification/store.ts`

**Interfaces:**
- Produces: `importLegacyCase(userId, legacyCaseId, actionId)` returning one `migration_waived` v3 case linked by `importedFromCaseId`.

- [ ] **Step 1: Add failing import tests**

Cover v2 and legacy inputs; preserve declared profile, latest candidate range, scoreable historical events, and baseline active time; do not import current choice prompt as evidence; repeated import returns the same v3 case; completed/abandoned cases cannot be silently resumed.

- [ ] **Step 2: Run and verify failure**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/conversational-legacy-import.test.ts
```

Expected: FAIL because import support is absent.

- [ ] **Step 3: Implement read-only import**

Load the old case through existing loaders, project only declared input/current range/valid life events/baseline active time, create a v3 revision with `migration_waived`, and generate a fresh rich first turn from the inherited technical packet. Never mutate the old row or show its generic question.

- [ ] **Step 4: Run tests and commit**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/conversational-legacy-import.test.ts
git add frontend/src/lib/conversational-rectification/legacy-import.ts \
  frontend/src/lib/conversational-rectification/orchestrator.ts \
  frontend/src/lib/conversational-rectification/store.ts \
  frontend/tests/conversational-legacy-import.test.ts
git commit -m "feat: import unfinished birth-time cases"
```

### Task 12: Add authenticated E2E coverage, telemetry, and rollout gates

**Files:**
- Create: `frontend/tests/conversational-rectification-e2e.test.ts`
- Create: `tests/test_conversational_rectification_security.py`
- Modify: `frontend/src/lib/birth-time-journey-telemetry.ts`
- Modify: `frontend/src/app/api/health/route.ts`
- Modify: `deploy/README.md`
- Modify: `docs/research/user_reported_birth_time_flow_issues_2026_07_20.md`

**Interfaces:**
- Produces: synthetic end-to-end acceptance, no-PII telemetry categories, deployment/rollback runbook, and issue closure evidence.

- [ ] **Step 1: Add complete synthetic E2E scenarios**

Cover: onboarding skip; unverified-current-chat consent; rectify-first saved question; rich first turn; A/B/C domain selection plus free text; “都不符合”; clear and ambiguous evidence; pause/reload/new-device resume; single fixed charge; re-rectification old-time preservation; atomic candidate confirm; ordinary question continuation; chat deletion with case survival; transient 502 retry and Chinese error fallback.

- [ ] **Step 2: Add security contract tests**

Assert service-role-only tables/RPCs, owner/version/action guards, private candidate weights absent from public response, no secret-shaped fixture values, and future evidence excluded from scoring.

- [ ] **Step 3: Run focused full suites**

```bash
node --import ./frontend/node_modules/tsx/dist/loader.mjs --test frontend/tests/*.test.ts
.venv/bin/python -m pytest \
  tests/test_conversational_rectification_contract.py \
  tests/test_conversational_rectification_security.py \
  tests/test_birth_time_dynamic_persistence_contract.py -q
cd frontend && npm run lint
cd frontend && npm run build
```

Expected: all Node/Python tests PASS, ESLint exits 0, Next production build succeeds.

- [ ] **Step 4: Add privacy-safe telemetry and health fields**

Record only protocol, phase, action kind, result category, latency bucket, billing state, error category, and deployment SHA. Do not log narrative, event text, birth data, email, user ID, access token, or model prompt.

- [ ] **Step 5: Document rollout and rollback**

Update `deploy/README.md` with migration ordering, health verification, synthetic start/answer/pause/confirm smoke sequence, and rollback behavior: stop creating v3 cases, keep v3 reads/resume available, never downgrade or delete v3 rows, and preserve old active times.

- [ ] **Step 6: Close the recorded issues with evidence**

For ISSUE-BT-001 through ISSUE-BT-005, add the exact migration/test/deployment artifact that proves closure. Keep status open for any item not demonstrated by an authenticated production or equivalent local Supabase E2E.

- [ ] **Step 7: Commit**

```bash
git add frontend/tests/conversational-rectification-e2e.test.ts \
  tests/test_conversational_rectification_security.py \
  frontend/src/lib/birth-time-journey-telemetry.ts \
  frontend/src/app/api/health/route.ts deploy/README.md \
  docs/research/user_reported_birth_time_flow_issues_2026_07_20.md
git commit -m "test: verify conversational birth-time rectification"
```

## Final Verification Gate

- [ ] Confirm `git diff --check` is clean.
- [ ] Confirm no migration grants v3 case/turn/evidence tables or mutation RPCs to `authenticated`.
- [ ] Confirm a synthetic first turn contains candidate boundary, stable/sensitive layers, domain rationale, and dated historical-event request.
- [ ] Confirm the old generic broad-year questionnaire is unreachable for newly created cases.
- [ ] Confirm unfinished legacy cases import once with `migration_waived` and retain read-only history.
- [ ] Confirm start failure refunds, replay does not recharge, and resume/retry do not recharge.
- [ ] Confirm chat deletion succeeds and does not cascade to a rectification case.
- [ ] Confirm re-rectification leaves the prior active time unchanged until atomic confirmation.
- [ ] Confirm a transient deployment error never exposes raw English browser text.
- [ ] Confirm production health reports the deployed Git SHA before rollout is declared successful.
