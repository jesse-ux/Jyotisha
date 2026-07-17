# Multi-Model Chat Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let signed-in users choose a server-configured language model per chat session without exposing provider credentials or breaking the existing credit settlement rules.

**Architecture:** A server-only catalog parses `LLM_MODELS_JSON`, resolves referenced secret environment variables, and exposes only sanitized metadata through an authenticated endpoint. The browser stores only a stable model ID in each Supabase chat session and submits that ID with a consultation; the server resolves it before reserving a credit and selects a cached Mastra Agent for that model.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript 5, Zod 3, Mastra 1.50, Base UI Popover, Supabase Postgres/RLS, Node test runner, CSS design tokens.

## Global Constraints

- Local secrets live only in `frontend/.env.local`; production secrets live only in `/opt/jyotisha-app/.env.production`.
- Never expose provider URLs, API model IDs, secret environment-variable names, or credentials through browser payloads or logs.
- Model selection is remembered per session and may change only between messages.
- Onboarding always uses the configured default model.
- Every enabled model costs exactly one credit in this release.
- Resolve and reject an unknown model before calling `begin_consultation_credit`.
- Preserve the existing free undo, pre-output refund, and post-output charged-stop behavior.
- Follow `frontend/DESIGN.md`; no new raw color, typography, spacing, shadow, or motion token.
- Preserve unrelated dirty files owned by other agents.

---

### Task 1: Server Model Catalog

**Files:**
- Modify: `frontend/src/mastra/model.ts`
- Create: `frontend/tests/model-catalog.test.ts`
- Modify: `frontend/README.md`
- Modify: `deploy/README.md`

**Interfaces:**
- Produces: `resolveLanguageModelCatalog(environment)`, `languageModelCatalog`, `resolveLanguageModel(modelId)`, `defaultLanguageModel()`, `publicLanguageModelCatalog()`.
- Produces public shape: `{ id, label, description, creditCost: 1, isDefault }`.
- Consumes: `MastraModelConfig`, Zod, `NodeJS.ProcessEnv`.

- [ ] **Step 1: Write failing catalog tests**

Add tests for a two-model catalog, secret redaction, invalid entries, unknown defaults, and legacy single-model fallback:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { resolveLanguageModelCatalog } from "../src/mastra/model.ts";

test("resolves two configured models while returning sanitized public metadata", () => {
  // Given
  const environment = {
    LLM_DEFAULT_MODEL_ID: "deepseek-pro",
    LLM_MODELS_JSON: JSON.stringify([
      {
        id: "deepseek-pro",
        label: "DeepSeek V4 Pro",
        description: "复杂分析",
        provider: "openai-compatible",
        baseURL: "https://api.deepseek.com",
        apiKeyEnv: "DEEPSEEK_API_KEY",
        model: "deepseek-v4-pro",
        creditCost: 1,
      },
      {
        id: "gpt-mini",
        label: "ChatGPT Mini",
        description: "均衡响应",
        provider: "openai",
        apiKeyEnv: "OPENAI_API_KEY",
        model: "openai/gpt-5-mini",
        creditCost: 1,
      },
    ]),
    DEEPSEEK_API_KEY: "deepseek-secret",
    OPENAI_API_KEY: "openai-secret",
  };

  // When
  const catalog = resolveLanguageModelCatalog(environment);

  // Then
  assert.equal(catalog.defaultModelId, "deepseek-pro");
  assert.deepEqual(catalog.publicModels[0], {
    id: "deepseek-pro",
    label: "DeepSeek V4 Pro",
    description: "复杂分析",
    creditCost: 1,
    isDefault: true,
  });
  assert.equal(JSON.stringify(catalog.publicModels).includes("secret"), false);
  assert.equal(JSON.stringify(catalog.publicModels).includes("baseURL"), false);
});
```

- [ ] **Step 2: Run the catalog test and verify RED**

Run: `cd frontend && node --test tests/model-catalog.test.ts`

Expected: FAIL because `resolveLanguageModelCatalog` is not exported.

- [ ] **Step 3: Implement the catalog parser and resolver**

Use a Zod boundary for each raw catalog item and return immutable resolved entries. OpenAI entries produce a Mastra model string; OpenAI-compatible entries produce `{ providerId, modelId, url, apiKey }`. Resolve `apiKeyEnv` only on the server. Invalid items are excluded with redacted issue codes. If `LLM_MODELS_JSON` is absent, derive one entry from the shipped `LLM_*` or `OPENAI_*` variables.

The catalog result must have this contract:

```ts
export type PublicLanguageModel = {
  readonly id: string;
  readonly label: string;
  readonly description: string;
  readonly creditCost: 1;
  readonly isDefault: boolean;
};

export type ResolvedLanguageModel = PublicLanguageModel & {
  readonly model: MastraModelConfig;
};

export type LanguageModelCatalog = {
  readonly models: readonly ResolvedLanguageModel[];
  readonly publicModels: readonly PublicLanguageModel[];
  readonly defaultModelId: string | null;
  readonly issues: readonly string[];
};
```

- [ ] **Step 4: Run catalog tests and type checking**

Run: `cd frontend && node --test tests/model-catalog.test.ts && npx tsc --noEmit`

Expected: all catalog tests PASS and TypeScript exits `0`.

- [ ] **Step 5: Document configuration**

Update `frontend/README.md` and `deploy/README.md` with `LLM_MODELS_JSON`, `LLM_DEFAULT_MODEL_ID`, one secret environment variable per provider, and the existing single-model fallback. Use redacted values only. Do not add `frontend/.env.example`: the repository intentionally ignores all `.env*` files.

- [ ] **Step 6: Commit the catalog task**

```bash
git add frontend/src/mastra/model.ts frontend/tests/model-catalog.test.ts frontend/README.md deploy/README.md docs/superpowers/plans/2026-07-17-multi-model-chat-selection.md
git commit -m "feat: add server model catalog"
```

---

### Task 2: Authenticated Model Endpoint and Agent Selection

**Files:**
- Create: `frontend/src/app/api/models/route.ts`
- Modify: `frontend/src/mastra/index.ts`
- Modify: `frontend/src/app/api/consult/route.ts`
- Modify: `frontend/src/app/api/onboarding/route.ts`
- Create: `frontend/tests/public-models.test.ts`
- Create: `frontend/src/lib/public-models.ts`

**Interfaces:**
- Consumes: catalog functions from Task 1.
- Produces: `GET /api/models -> { models, defaultModelId }` after Supabase authentication.
- Produces: `getJyotishAgent(model)` and `getOnboardingAgent(model)` process-local caches.
- Consultation request consumes `modelId: string`.

- [ ] **Step 1: Write failing public payload tests**

Create a Zod client boundary that accepts only the sanitized response and rejects routing fields:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { parsePublicModelCatalog } from "../src/lib/public-models.ts";

test("parses a sanitized public model catalog", () => {
  // Given
  const payload = {
    defaultModelId: "deepseek-pro",
    models: [{
      id: "deepseek-pro",
      label: "DeepSeek V4 Pro",
      description: "复杂分析",
      creditCost: 1,
      isDefault: true,
    }],
  };

  // When
  const catalog = parsePublicModelCatalog(payload);

  // Then
  assert.equal(catalog.defaultModelId, "deepseek-pro");
  assert.equal(catalog.models.length, 1);
});
```

- [ ] **Step 2: Run the payload test and verify RED**

Run: `cd frontend && node --test tests/public-models.test.ts`

Expected: FAIL because the parser module does not exist.

- [ ] **Step 3: Implement the public parser and authenticated route**

`parsePublicModelCatalog(value: unknown)` must use strict Zod objects so additional secret or routing fields are rejected. `GET /api/models` must authenticate through `createServerSupabaseClient`, return `401` when logged out, `503` when the catalog has no default, and otherwise return the sanitized catalog.

- [ ] **Step 4: Refactor Mastra Agent construction**

Move the existing shared instructions into constants and build Agents through keyed factories:

```ts
const jyotishAgents = new Map<string, Agent>();

export function getJyotishAgent(model: ResolvedLanguageModel) {
  const cached = jyotishAgents.get(model.id);
  if (cached) return cached;
  const agent = new Agent({
    id: `jyotish-guide-${model.id}`,
    name: "Jyotish Guide",
    model: model.model,
    instructions: jyotishInstructions,
    skills: [jyotishSkillPath],
    tools: { consultationTool },
  });
  jyotishAgents.set(model.id, agent);
  return agent;
}
```

Create the onboarding Agent with the default resolved model and keep its existing instructions unchanged.

- [ ] **Step 5: Select the model before credit reservation**

Extend `chatRequestSchema` with `modelId: z.string().trim().min(1).max(64)`. Resolve the ID after authentication, request parsing, and prompt-extraction blocking, but before `begin_consultation_credit`. Return `409` with a safe message for an unavailable model. Use `getJyotishAgent(resolvedModel)` for streaming and record `resolvedModel.id` in `credit_transactions`.

- [ ] **Step 6: Run tests, type checking, and lint**

Run: `cd frontend && npm test && npx tsc --noEmit && npm run lint`

Expected: all tests PASS; type checking and lint exit `0`.

- [ ] **Step 7: Commit the endpoint task**

```bash
git add frontend/src/app/api/models/route.ts frontend/src/lib/public-models.ts frontend/tests/public-models.test.ts frontend/src/mastra/index.ts frontend/src/app/api/consult/route.ts frontend/src/app/api/onboarding/route.ts
git commit -m "feat: route consultations by model"
```

---

### Task 3: Session Model Persistence

**Files:**
- Create: `frontend/supabase/migrations/20260717010000_chat_session_model.sql`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/lib/public-models.ts`
- Modify: `frontend/tests/public-models.test.ts`

**Interfaces:**
- Consumes: `PublicLanguageModelCatalog` from Task 2.
- Produces: `resolveSessionModelId(saved, catalog) -> { modelId, fellBack }`.
- Persists: `chat_sessions.model_id text`.

- [ ] **Step 1: Write failing session fallback tests**

```ts
test("falls back to the configured default when a saved model is removed", () => {
  // Given
  const catalog = parsePublicModelCatalog({
    defaultModelId: "deepseek-pro",
    models: [{
      id: "deepseek-pro",
      label: "DeepSeek V4 Pro",
      description: "复杂分析",
      creditCost: 1,
      isDefault: true,
    }],
  });

  // When
  const result = resolveSessionModelId("removed-model", catalog);

  // Then
  assert.deepEqual(result, { modelId: "deepseek-pro", fellBack: true });
});
```

- [ ] **Step 2: Run the fallback test and verify RED**

Run: `cd frontend && node --test tests/public-models.test.ts`

Expected: FAIL because `resolveSessionModelId` does not exist.

- [ ] **Step 3: Implement fallback and migration**

Add nullable `model_id text` to `public.chat_sessions` and grant authenticated users column-level insert/update access. Do not store labels, provider fields, or secrets.

`resolveSessionModelId` returns the saved ID when it is in the catalog and otherwise returns the default with `fellBack: true`.

- [ ] **Step 4: Wire persistence into the page**

Extend `ChatSession` with `modelId`. Fetch `/api/models` during bootstrap, parse it through `parsePublicModelCatalog`, normalize loaded sessions, and persist fallback replacements once. New sessions use `defaultModelId`; `persistSession` reads/writes `model_id`; consultation requests include the active session's `modelId`.

Preview mode must install a deterministic two-model catalog so browser QA can run without provider keys.

- [ ] **Step 5: Run focused tests and build**

Run: `cd frontend && npm test && npx tsc --noEmit && npm run build`

Expected: tests PASS and production build exits `0`.

- [ ] **Step 6: Commit persistence**

```bash
git add frontend/supabase/migrations/20260717010000_chat_session_model.sql frontend/src/app/page.tsx frontend/src/lib/public-models.ts frontend/tests/public-models.test.ts
git commit -m "feat: persist session model choice"
```

---

### Task 4: Composer Model Selection Bubble

**Files:**
- Create: `frontend/src/components/model-selector.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/DESIGN.md`

**Interfaces:**
- Consumes: `readonly PublicLanguageModel[]`, selected ID, disabled state, selection callback.
- Produces: accessible Base UI Popover with native radio inputs.

- [ ] **Step 1: Add the model-selector primitive to `DESIGN.md`**

Document the compact trigger, upward warm-canvas popup, radio rows, 44px touch target, focus behavior, disabled request states, and existing motion/token usage before writing JSX or CSS.

- [ ] **Step 2: Add the component in preview mode and observe RED behavior**

Render a temporary import of the not-yet-created `ModelSelector` in the composer footer and run `cd frontend && npx tsc --noEmit`.

Expected: FAIL because `frontend/src/components/model-selector.tsx` does not exist.

- [ ] **Step 3: Implement the Base UI Popover**

Use `Popover.Root`, `Trigger`, `Portal`, `Positioner side="top" align="start"`, and `Popup`. Render a `role="radiogroup"` whose rows contain controlled native radio inputs. Selecting an item closes the popup and invokes the supplied callback. Base UI owns Escape, outside press, focus restoration, and collision positioning.

Component contract:

```ts
type ModelSelectorProps = {
  readonly models: readonly PublicLanguageModel[];
  readonly selectedModelId: string;
  readonly disabled: boolean;
  readonly onSelect: (modelId: string) => void;
};
```

- [ ] **Step 4: Persist selection from the page**

Place the trigger below `.composer` and before the status line. Optimistically update the active session, persist it immediately, retain the visible choice on sync failure, and show a retryable composer notice. Disable selection while undo, streaming, cancellation, session creation, or model loading is active.

- [ ] **Step 5: Style entirely from existing design tokens**

Add `.composer-tools`, `.model-selector-*` rules using current canvas, border, ink, radius, spacing, shadow, type, and 120/180ms motion tokens. Constrain the popup to the viewport and keep each row at least 44px. Add reduced-motion behavior through the existing media query.

- [ ] **Step 6: Run static verification**

Run: `cd frontend && npm test && npx tsc --noEmit && npm run lint && npm run build`

Expected: all commands exit `0`.

- [ ] **Step 7: Commit the UI task**

```bash
git add frontend/src/components/model-selector.tsx frontend/src/app/page.tsx frontend/src/app/globals.css frontend/DESIGN.md
git commit -m "feat: add chat model selector"
```

---

### Task 5: Migration, Runtime QA, Slop Audit, and Delivery

**Files:**
- Modify only if verification exposes a defect in files already owned by Tasks 1–4.

**Interfaces:**
- Consumes the complete feature.
- Produces fresh test, browser, migration, security, and deployment evidence.

- [ ] **Step 1: Run the complete relevant verification set**

```bash
cd frontend
npm test
npx tsc --noEmit
npm run lint
npm run build
```

Run focused repository contracts from the repository root:

```bash
.venv/bin/python -m pytest -q \
  tests/test_supabase_user_data_contract.py \
  tests/test_agent_chat_contract.py \
  tests/test_railway_deployment.py \
  tests/test_frontend_theme_contract.py
```

Expected: all relevant checks PASS. Name any unrelated pre-existing failure without modifying it.

- [ ] **Step 2: Apply and verify the Supabase migration**

Run: `cd frontend && npx supabase db push --linked`

Then run: `npx supabase migration list --linked`

Expected: local and remote both list `20260717010000`.

- [ ] **Step 3: Run real browser QA**

Start the production-like app with preview data, then drive it through the in-app browser or Playwright at 375px, 768px, and 1280px. Verify open/close, radio keyboard behavior, Escape, focus return, model switching, per-session persistence, disabled state during undo/streaming, no horizontal overflow, and no console errors. Inspect the `/api/models` payload to confirm no provider routing or secret fields are present.

- [ ] **Step 4: Run the requested AI-slop audit**

Run:

```bash
node ../.agents/skills/kill-ai-slop/scripts/scan.mjs frontend/src --json
```

Review every hit against `frontend/DESIGN.md`; fix confirmed slop and retain only deliberate, documented patterns.

- [ ] **Step 5: Run final review and debugging gates**

Review goal coverage, QA evidence, code quality, security, and missed context. Record at least three runtime hypotheses and the evidence that ruled each in or out. Fix every blocking finding and rerun only the checks whose inputs changed.

- [ ] **Step 6: Commit verification fixes**

If verification required changes, stage only feature-owned files and commit them with a focused `fix:` message. If no files changed, do not create an empty commit.

- [ ] **Step 7: Publish through the user-selected Git workflow**

After fresh verification, preserve unrelated work, inspect branch/upstream state, and use the finishing-a-development-branch workflow. Push only after the feature commits and migration evidence are complete; if merged to `main`, monitor CI and production deployment through the existing workflows and run the production smoke checks documented in `deploy/README.md`.
