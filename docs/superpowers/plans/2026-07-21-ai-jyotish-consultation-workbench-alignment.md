# AI Jyotish consultation workbench alignment

Date: 2026-07-21

Commercial repo: `/Users/wuyongnaren/Documents/Jyotisha-commercial`

Research truth source: `/Users/wuyongnaren/Documents/印度占星`

Current commercial branch observed: `codex/fix-chat-session-deletion`

## Product target

Upgrade the commercial Jyotish website from a form/report/chat surface into an AI astrology consultation workbench:

- guided topics when users do not know what to ask;
- strict workflow routing for career, marriage, wealth, timing, rectification and general readings;
- visible evidence chain, parameter freeze, confidence and claim boundary;
- follow-up prompts after every answer;
- privacy-safe commercial runtime without writing user birth data or private cases into public artifacts.

This is not a UI-only optimization. UI work is downstream of runtime identity, evidence gates and workflow routing.

## Current architecture observed

### Frontend

- Main page: `frontend/src/app/page.tsx`
- Global styles: `frontend/src/app/globals.css`
- Sidebar/session UI:
  - `frontend/src/components/app-sidebar.tsx`
  - `frontend/src/components/sidebar-session-row.tsx`
- Message rendering:
  - `frontend/src/components/chat-message-row.tsx`
  - `frontend/src/components/chat-message-content.tsx`
- Birth-time journey UI:
  - `frontend/src/components/birth-time-intake.tsx`
  - `frontend/src/components/birth-time-guide-turn.tsx`
  - `frontend/src/components/birth-time-choice-question.tsx`
  - `frontend/src/components/birth-time-candidate-result.tsx`
  - `frontend/src/components/birth-time-evidence-draft-card.tsx`

### API routes

- Chat/consultation: `frontend/src/app/api/consult/route.ts`
- Health check: `frontend/src/app/api/health/route.ts`
- Daily star language: `frontend/src/app/api/daily-starlanguage/route.ts`
- Chart profiles: `frontend/src/app/api/chart-profiles/route.ts`
- Birth-time guide: `frontend/src/app/api/birth-time-guide/route.ts`
- Birth-time journey: `frontend/src/app/api/birth-time-journey/route.ts`
- Birth rectification: `frontend/src/app/api/birth-rectification/route.ts`

### Workflow and safety layer

- Workflow projection: `frontend/src/lib/consultation-workflow-request.ts`
- Entrypoint question resolver: `frontend/src/lib/consultation-entrypoint.ts`
- Safety guard: `frontend/src/lib/consult-safety.ts`
- Timing boundary guard: `frontend/src/lib/timing-output-guard.ts`
- Agent reply and streaming:
  - `frontend/src/lib/agent-reply.ts`
  - `frontend/src/lib/stream-text-response.ts`

### Existing tests already relevant

- `frontend/tests/consultation-workflow-contract.test.ts`
- `frontend/tests/consultation-workflow-request.test.ts`
- `frontend/tests/starter-questions.test.ts`
- `frontend/tests/chat-stream-layout.test.ts`
- `frontend/tests/birth-time-mobile-scroll-contract.test.ts`
- `frontend/tests/birth-time-journey-*.test.ts`
- `frontend/tests/timing-output-guard.test.ts`
- `frontend/tests/jyotish-api-reachability-contract.test.ts`

## Gap summary

| Layer | Current state | Gap |
|---|---|---|
| Truth source identity | `/api/health` reports web/env/model/Jyotish API status and git commit | Does not expose research truth source path, research commit, evidence packet count, oracle summary or claim gate status |
| Guided topics | Starter questions and private entrypoints exist | Topics are not yet generated from profile completeness + question intent + strict workflow evidence requirements |
| Strict workflow routing | `consultation-workflow-request.ts` maps broad themes | Timing currently maps to career; missing explicit route taxonomy for rectification, health, annual/monthly timing, Prashna, compatibility |
| Evidence display | Birth-time evidence components exist | No general consultation evidence panel/audit table for D1/D9/D10/Dasha/Narayana/Transit/Shadbala/AV/Jaimini/UL/DK/A10 |
| Parameter freeze | Some backend headers expose workflow status | UI does not consistently show Ayanamsa, node mode, timezone, coordinates, birth-time precision and calculation source |
| Claim boundary | Timing guard exists | Need runtime gate that prevents blocked/partial/oracle-missing claims from rendering as definitive predictions |
| Layout maturity | Chat shell exists | Composer can visually drift/overlay content; workbench should reserve bottom space and use stable scroll container |
| Privacy | Commercial repo has Supabase/business flow | Need explicit artifact filter and CI guard to prevent private birth data/events from entering public fixtures |

## P0 implementation plan

### P0-1 — Runtime identity and capability status

Goal: the site must show what capability source it is using.

Files:

- Add `frontend/src/lib/truth-source-runtime-identity.ts`
- Add or extend `frontend/src/app/api/health/route.ts`
- Add `frontend/tests/truth-source-runtime-identity.test.ts`
- Add `frontend/tests/health-deployment.test.ts` assertions

Contract:

```json
{
  "truthSource": {
    "path": "/Users/wuyongnaren/Documents/印度占星",
    "commit": "...",
    "skillVersion": "...",
    "evidencePacketCount": 120,
    "oracleSummary": {
      "ready": [],
      "partial": [],
      "blocked": []
    },
    "claimGateStatus": "partial_or_blocked_present"
  }
}
```

Rules:

- Do not read private user artifacts.
- Do not require the production container to mount the local research repo; if absent, report `not_mounted`, not `ok`.
- Do not claim synced when git/packet metadata cannot be read.

### P0-2 — Workbench shell layout fix

Goal: stop the composer from floating over forms/content and make the page feel like a stable consultation tool.

Files:

- `frontend/src/app/page.tsx`
- `frontend/src/app/globals.css`
- `frontend/tests/chat-stream-layout.test.ts`
- `frontend/tests/birth-time-mobile-scroll-contract.test.ts`

Contract:

- One scroll container for conversation/workbench content.
- Composer pinned inside the main column, not viewport-floating across sidebar.
- Content bottom padding equals composer height.
- Onboarding/profile forms cannot appear underneath the composer.

### P0-3 — Guided topic cards

Goal: when user lacks a question, show 3-5 useful consultation cards with evidence preview.

Files:

- Add `frontend/src/lib/guided-jyotish-topics.ts`
- Extend `frontend/src/lib/consultation-entrypoint.ts`
- Extend `frontend/src/app/page.tsx`
- Extend `frontend/tests/starter-questions.test.ts`

Initial topics:

- Career phase and next leverage point
- Relationship pattern and partnership timing boundary
- Wealth structure and risk point
- Current year/month broad timing window
- Birth-time confidence check

Each topic must carry:

- `theme`
- `visibleQuestion`
- `strictWorkflowRoute`
- `evidencePreview`
- `confidenceCap`
- `claimBoundary`

### P0-4 — Strict workflow route contract

Goal: every user question must route to an explicit Jyotish workflow before the agent speaks.

Files:

- Extend `frontend/src/lib/consultation-workflow-request.ts`
- Extend `frontend/src/app/api/consult/route.ts`
- Extend `frontend/tests/consultation-workflow-contract.test.ts`
- Extend `frontend/tests/consultation-workflow-request.test.ts`

Routes:

- `career`: D1, D10, 10th house/lord, A10, AmK, Vimshottari, Narayana, transit
- `marriage`: D1, D9, 7th house/lord, Venus/Jupiter, DK, UL, A7, Vimshottari, Narayana, transit
- `wealth`: D1, D2, D11, 2nd/11th/9th/5th, wealth yogas, AV, Dasha
- `timing`: Dasha + Narayana + transit + varga; day/month remains candidate unless holdout passes
- `rectification`: D1 boundary, D9/D10/D12/D60 sensitivity, event backtest, candidate not truth
- `prashna`: question time/place/timezone/ayanamsa/node mode; observation only until oracle packets close
- `general`: broad multi-domain reading with clear missing layers

### P0-5 — Claim gate display

Goal: users can still receive dates/windows, but the UI must not package exploratory candidates as verified prediction.

Files:

- `frontend/src/lib/timing-output-guard.ts`
- `frontend/src/components/chat-message-content.tsx`
- Add `frontend/src/components/claim-boundary-badge.tsx`
- Tests:
  - `frontend/tests/timing-output-guard.test.ts`
  - `frontend/tests/consultation-workflow-contract.test.ts`

Statuses:

- `verified_window`
- `candidate_day_window`
- `exploratory_unvalidated`
- `observation_only`
- `blocked_until_oracle`
- `blocked_until_human_labels`

## P1 implementation plan

### P1-1 — Evidence panel / Technique Audit Table

Files:

- Add `frontend/src/components/evidence-audit-panel.tsx`
- Extend `frontend/src/components/chat-message-content.tsx`
- Add `frontend/tests/evidence-audit-panel.test.ts`

Rows:

- D1
- D9 / D10 / D2 / D11 as applicable
- Vimshottari Dasha
- Narayana Dasha
- Transit / Gochara
- Shadbala
- Ashtakavarga
- Jaimini: DK, AmK, UL, A7, A10
- Functional Benefic/Malefic
- MEVG / Global Web Evidence
- Real Case Calibration

### P1-2 — Report export

Files:

- Add `frontend/src/lib/consultation-report-export.ts`
- Add export button in message/report view
- Add `frontend/tests/consultation-report-export.test.ts`

Export must include:

- frozen parameters;
- conclusion;
- evidence table;
- conflict points;
- claim boundary;
- follow-up questions.

### P1-3 — Privacy artifact filter

Files:

- Add `scripts/commercial_privacy_artifact_scan.py`
- Add `tests/test_commercial_privacy_artifact_scan.py`
- Wire into commercial CI.

Rules:

- Reject real user names, exact birth data, private location/event text in fixtures.
- Allow public-person examples only with source tag.
- Mark imported research oracle packets as non-user artifacts.

## P2 implementation plan

### P2-1 — Visual polish after P0/P1

Files:

- `frontend/src/app/page.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/components/app-sidebar.tsx`

Direction:

- Keep original warm color palette.
- Use commercial site layout language, but make the homepage cards smaller, lower, and easier to click.
- Do not put birth-time rectification as an oversized floating block.

### P2-2 — Commercial sync discipline

Files:

- Add `docs/research_sync_contract.md`
- Add `frontend/tests/research-truth-source-contract.test.ts`

Rules:

- Commercial repo consumes mature research contracts.
- Commercial repo does not copy private WorkBuddy fragments.
- WorkBuddy backups remain `historical_fragment_only`.

## First landing sequence

1. Implement P0-1 runtime identity endpoint and test.
2. Implement P0-2 layout contract to fix composer drift.
3. Implement P0-3 guided topics as deterministic cards.
4. Implement P0-4 strict workflow route taxonomy.
5. Implement P0-5 claim boundary badge.
6. Run focused frontend tests.
7. Only then start P1 evidence panel.

## Current blocker / caution

`/private/tmp/jyotisha-optimize` from the pasted request does not exist on this machine. The active commercial candidate is `/Users/wuyongnaren/Documents/Jyotisha-commercial`.

The commercial worktree currently has untracked `hip_main.dat` and `hip_main.dat.download`. They look like local ephemeris/runtime assets and should not be committed unless explicitly reviewed.
