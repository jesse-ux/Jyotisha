# Multi-Model Chat Selection Design

Date: 2026-07-17
Status: Approved in conversation; awaiting written-spec review

## 1. Goal

Allow a signed-in user to choose which configured language model answers the next message in a chat session. The selected model is remembered per session, may be changed between messages, and never exposes provider credentials or arbitrary provider URLs to the browser.

The first release supports DeepSeek and OpenAI while keeping the provider layer generic enough for additional OpenAI-compatible models. Every enabled model costs one consultation credit in this release. The catalog still carries `creditCost` so differentiated pricing can be introduced deliberately later.

## 2. Product Decisions

- Model selection is stored per chat session and synchronized through Supabase.
- A user may switch models before any new message; the switch affects only the next and later messages.
- Existing message history is sent normally after a switch.
- Model selection is disabled during the undo window, streaming, cancellation, and settlement.
- Onboarding generation uses the server-configured default model, not the active session model.
- Every enabled model costs one credit in the first release.
- Provider keys remain server-only. The client submits only a catalog model ID.

## 3. Configuration

### 3.1 Locations

- Local development: `frontend/.env.local`
- Production: `/opt/jyotisha-app/.env.production`

Neither file is committed. Model secrets must never use a `NEXT_PUBLIC_` prefix.

### 3.2 Catalog shape

`LLM_MODELS_JSON` contains non-secret routing metadata and references a separate environment variable for each key:

```dotenv
LLM_DEFAULT_MODEL_ID=deepseek-pro

LLM_MODELS_JSON='[
  {
    "id": "deepseek-pro",
    "label": "DeepSeek V4 Pro",
    "description": "更适合复杂分析",
    "provider": "openai-compatible",
    "baseURL": "https://api.deepseek.com",
    "apiKeyEnv": "DEEPSEEK_API_KEY",
    "model": "deepseek-v4-pro",
    "creditCost": 1
  },
  {
    "id": "gpt-5-mini",
    "label": "ChatGPT 5 Mini",
    "description": "响应稳定、速度均衡",
    "provider": "openai",
    "apiKeyEnv": "OPENAI_API_KEY",
    "model": "openai/gpt-5-mini",
    "creditCost": 1
  }
]'

DEEPSEEK_API_KEY=<server-secret>
OPENAI_API_KEY=<server-secret>
```

Catalog validation requires:

- unique, stable, URL-safe IDs;
- non-empty labels and model identifiers;
- a supported provider value;
- an HTTPS `baseURL` for OpenAI-compatible providers;
- an existing non-empty environment variable named by `apiKeyEnv`;
- `creditCost` equal to `1` in this release;
- a default ID that resolves to an enabled model.

An invalid catalog item is excluded from the public list and recorded through a redacted server warning. Secrets, complete configuration objects, and secret environment-variable values are never logged.

### 3.3 Existing configuration compatibility

If `LLM_MODELS_JSON` is absent, the server derives one default catalog item from the shipped single-model configuration:

- `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, and optional `LLM_PROVIDER_ID`; or
- `OPENAI_API_KEY` and `MASTRA_MODEL`.

This preserves the current production deployment while allowing migration to the multi-model catalog. Once the catalog is present, it is authoritative and the legacy variables do not create additional choices.

## 4. Server Architecture

### 4.1 Model catalog module

Replace the current import-time singleton with a server-only catalog module responsible for:

- parsing and validating configuration;
- returning sanitized public metadata;
- resolving a submitted model ID to a Mastra model configuration;
- resolving the default model;
- reporting configuration problems without including secrets.

The public model shape is limited to:

```ts
type PublicModel = {
  id: string;
  label: string;
  description: string;
  creditCost: 1;
  isDefault: boolean;
};
```

### 4.2 Agent creation

The Jyotish agent instructions, skills, and tools remain shared. Agent construction becomes a factory keyed by the resolved catalog model. A process-local cache avoids rebuilding an identical Agent for every request.

The onboarding agent is created from the default model. A session choice never changes onboarding generation.

### 4.3 Public models endpoint

`GET /api/models`:

- requires a valid Supabase user session;
- returns only enabled `PublicModel` items and the default ID;
- returns `503` with a safe message when no model is configured;
- never returns provider URLs, provider identifiers, model API identifiers, environment-variable names, or credentials.

### 4.4 Consultation endpoint

`POST /api/consult` accepts a bounded `modelId` string in addition to the current request fields.

Processing order:

1. authenticate the user;
2. validate the request shape and prompt safety;
3. resolve `modelId` against the server catalog;
4. reject unavailable models before any credit reservation;
5. reserve the consultation credit;
6. run the cached Agent for the resolved model;
7. settle using the existing undo, cancel, partial-output, and completion rules;
8. record the actual catalog model ID and token usage in `credit_transactions`.

The client cannot submit a base URL, provider, API model identifier, or key. An unknown or disabled model returns a client-safe error and does not consume a credit.

## 5. Persistence

Add a nullable `model_id text` column to `chat_sessions` through a Supabase migration.

- New sessions start with the current server default model ID.
- Selecting a model persists the changed session immediately.
- Existing rows with `NULL` resolve to the current default when read.
- If a stored ID is no longer available, the client selects the current default, persists it, and shows one non-blocking notice.
- No provider secret or provider configuration is stored in Supabase.

The existing RLS policy continues to restrict session changes to the owning user.

## 6. Composer Interaction

Add a lightweight toolbar directly below the composer field and above the existing status/help text.

### 6.1 Trigger

- Left-aligned compact text control: selected model label plus a downward chevron.
- Right-aligned keyboard hint remains available on desktop.
- The control uses the current warm canvas, hairline, typography, focus ring, and motion tokens from `frontend/DESIGN.md`.
- It is not rendered as a large pill and does not introduce a new palette or shadow token.

### 6.2 Selection bubble

- Opens upward from the trigger so it remains visible above the viewport bottom.
- Uses radio semantics with one checked model.
- Each row shows the public label, concise description, and `1 点/次`.
- Selecting an item closes the bubble, restores focus to the trigger, updates the session, and persists it.
- Escape closes without changing the selection.
- Outside click closes without changing the selection.
- Touch targets are at least 44px high.
- Mobile width is constrained to the viewport; desktop width remains compact.

### 6.3 Disabled states

The trigger and options are disabled while:

- a message is inside the 2.5-second free undo window;
- a response is streaming;
- cancellation or settlement is pending;
- session data or model catalog data is not yet ready.

The displayed label is therefore guaranteed to match the model attached to an active request.

## 7. Billing and Cancellation

All catalog models use one credit in this release. Model resolution occurs before `begin_consultation_credit`, so an invalid or removed model cannot reserve a credit.

After reservation, existing behavior remains authoritative:

- cancel before the first output chunk: refund idempotently;
- stop or fail after output begins: keep partial content and charge;
- complete normally: charge and record token usage;
- free undo before the API call: no model invocation and no charge.

The stored transaction model value is the stable catalog ID, not a user-supplied label.

## 8. Error Handling

- Catalog unavailable: disable sending and show a concise service-configuration message.
- Saved model removed: switch to default, persist, and show a one-time notice.
- Submitted model unknown: return a safe client error before billing; restore the question to the composer.
- Provider fails before output: use the existing cancellation/refund path.
- Provider fails after partial output: preserve the partial answer and complete billing.
- Session persistence fails after a local selection: keep the visible choice for the current page and show a retryable synchronization notice.

No error response contains provider credentials, provider URLs, environment-variable names, internal catalog objects, or stack traces.

## 9. Security Boundaries

- The catalog parser and model resolver are server-only modules.
- The browser receives an allowlist, not executable provider configuration.
- Submitted IDs are length-limited and matched exactly against the allowlist.
- Provider URLs cannot be influenced by request data, preventing request-level SSRF.
- API keys stay in server environment variables and are passed directly to the model SDK.
- Logs use catalog IDs and redacted validation codes only.
- `/api/models` requires authentication to avoid exposing operational inventory unnecessarily.

## 10. Verification

Automated coverage must prove:

- valid multi-model and legacy single-model configuration parsing;
- rejection of duplicates, missing keys, invalid URLs, and unknown defaults;
- sanitized `/api/models` output contains no secrets or server routing fields;
- unknown model rejection occurs before credit reservation;
- the selected catalog model reaches the Agent factory and usage ledger;
- session `model_id` round-trips through Supabase serialization;
- removed models fall back to the default;
- all cancellation and refund invariants remain unchanged.

Manual browser QA must exercise:

- opening and closing the model bubble;
- keyboard navigation, Escape, focus return, and radio state;
- switching models and sending the next message;
- session switching and page refresh persistence;
- disabled switching during undo and streaming;
- removed-model fallback messaging;
- 375px, 768px, and 1280px viewport layouts;
- console and network inspection confirming no credential or provider routing data reaches the browser.

## 11. Deployment

1. Apply the Supabase migration before deploying code that writes `model_id`.
2. Add `LLM_MODELS_JSON`, `LLM_DEFAULT_MODEL_ID`, and provider keys to `/opt/jyotisha-app/.env.production`.
3. Rebuild the web container; model configuration is read server-side at runtime.
4. Run CI, deploy through the existing `main` workflow, and verify `/api/models`, consultation billing, and internal health.

The first production catalog will expose DeepSeek V4 Pro and the selected OpenAI model. Their exact public labels and descriptions come from the server catalog, while their credentials remain only in the production environment file.
