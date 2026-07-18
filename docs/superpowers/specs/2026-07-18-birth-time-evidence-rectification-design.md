# Birth-Time Evidence Rectification Design

## Goal

Continue the deterministic birth-time journey after all questionnaire rounds are complete. The user supplies dated life events, a server-side engine compares those events against actual candidate chart differences, and the journey either asks for more evidence, saves a candidate interval, or permits an explicit confirmation. Agent prose never chooses a candidate, confidence level, route, or application permission.

This design extends `2026-07-17-birth-time-journey-design.md`. It does not replace the existing intake, sensitivity scan, or questionnaire.

## Current Failure and Root Cause

The current questionnaire ends with `nextRoundQuestions=[]`, while the snapshot still carries `input="rectification_questions"`. The UI consequently has nothing left to render and shows a saved-candidate terminal note.

This is not only a rendering bug. The existing scorer ranks abstract labels such as `middle_candidate_cluster`; it does not score actual candidate minutes against dated events. Its own boundary states that an event-to-candidate adjudication model is still required. Advancing directly to confirmation would therefore fabricate minute-level certainty.

## Scope

This delivery adds:

- a deterministic `collect_life_events` step after all questionnaire rounds;
- structured event collection for three to six dated events;
- actual candidate segments derived from local chart differences;
- a bounded local event-to-candidate scorer using fixed, versioned rules;
- conservative low, medium, and high confidence outcomes;
- candidate-result, add-evidence, save-candidate, and confirm-candidate states;
- a server-only application gate that updates `active_birth_time` only after a valid high-confidence result and explicit user confirmation;
- persistence, resume behavior, tests, and real-browser verification for the complete path.

It does not add free-form event interpretation, model-based event extraction, consultation billing, or claims that the selected minute is historically proven.

## State and Input Model

Journey states become:

- `rectifying`: questionnaire or event evidence is still required;
- `candidate`: a deterministic candidate result exists but is not active;
- `confirming`: the result passed the application threshold and awaits explicit confirmation;
- `ready`: an active time exists.

Journey inputs become:

- `rectification_questions`;
- `life_events`;
- `candidate_actions`;
- `candidate_confirmation`;
- `none`.

When the final questionnaire answer produces no next-round questions, the deterministic domain function must return:

```json
{
  "state": "rectifying",
  "assistantIntent": "collect_dated_life_events",
  "input": "life_events",
  "canApply": false,
  "activeTime": null
}
```

The UI must render from `input`; it must not infer that transition from answer counts.

## Life-Event Contract

Each event contains only structured evidence used by deterministic code:

```json
{
  "id": "client-generated-uuid",
  "domain": "career",
  "date": "2021-09",
  "precision": "month"
}
```

Supported domains and mandatory comparison layers are:

| Domain | Candidate layers |
| --- | --- |
| `education` | D24, houses 4/5/9 |
| `relocation` | D4, houses 4/12 |
| `relationship` | D9, house 7, UL/A7 when available |
| `career` | D10, house 10, A10 when available |
| `health_pressure` | D30, houses 6/8/12 |

Dates may use `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`; the declared precision must match the value. Dates before birth or after the current local date are rejected. At least three usable events across at least two domains are required before scoring; at most six events are stored in one case. Free-form notes are outside this delivery because they cannot affect deterministic scoring.

## Candidate Generation

The phase-two scanner uses the stored reported date, stored location, timezone, and reported range. The browser cannot supply or widen that range.

1. Scan the stored range at one-minute resolution with the repository's local domain calculation service.
2. Record D1, D4, D9, D10, D24, and D30 signatures. Compute UL, A7, A10, and KP cusp identifiers when their local implementations return valid values.
3. Collapse adjacent minutes with identical relevant signatures into contiguous candidate segments.
4. Select one deterministic representative minute per segment for event scoring. Preserve the full segment boundaries in the result.
5. Cap work to a full civil day and return a fail-closed result if required chart layers cannot be computed.

Candidate generation is server-side and versioned. Stored raw scan evidence must include settings, supported and unavailable layers, candidate segments, and the algorithm version.

## Event-to-Candidate Scoring

A new isolated Python module owns scoring. It may call existing local chart, Vimshottari, Narayana Dasha, Varga, and Arudha calculations, but it must not call a language model or external network service.

For each representative candidate and event:

1. Calculate the candidate natal chart and mandatory domain Varga.
2. Calculate Vimshottari and Narayana periods active at the declared event date.
3. Apply a checked-in, versioned rule table that scores whether active lords/signs connect to the domain houses and candidate-specific layers.
4. Apply only a precision weight: day `1.0`, month `0.8`, year `0.5`.
5. Emit per-event rule IDs and points. No narrative interpretation affects the score.

The aggregate result ranks candidate segments, not abstract early/middle/late clusters. Equal scores remain ties. Missing optional UL/A7/A10/KP layers lower the confidence ceiling and never award substitute points.

## Confidence and Application Gate

Confidence is deterministic and conservative:

- `low`: fewer than three usable events, fewer than two domains, a tied leader, missing a mandatory layer, a winning interval wider than 15 minutes, or a lead margin below 10 percent;
- `medium`: all evidence requirements pass, the winning interval is at most 15 minutes, and the lead margin is at least 10 percent;
- `high`: at least four usable events across at least three domains, no required layer is missing, the winning interval is at most 5 minutes, and the lead margin is at least 20 percent.

Percent margin is `(topScore - secondScore) / max(abs(topScore), 1)`. Threshold constants and their version are stored with the result.

Routing is:

- low: keep `input="life_events"`, explain the insufficiency, allow replacing or adding events, and keep `canApply=false`;
- medium: set `input="candidate_actions"`, allow saving the interval or adding evidence, and keep `canApply=false`;
- high: set `input="candidate_confirmation"` and `canApply=true`, but keep `activeTime=null` until confirmation.

`canApply=true` means only that the stored result is eligible for a confirmation event. It must never itself update the profile.

The response parser's current blanket rule that forbids `canApply=true` on every rectification route must be narrowed: it is valid only for `state="confirming"`, `input="candidate_confirmation"`, high confidence, and a non-null stored candidate result. Every other rectification response must keep it false.

## Confirmation

`confirm_candidate` accepts only `caseId`, the stored candidate result ID, and the stored representative time. The service reloads the case and rejects the event unless:

- the current snapshot is `confirming`;
- the stored result is high confidence;
- `canApply` is true;
- the result ID and time exactly match the stored winner;
- the case belongs to the authenticated user.

On success, one server-side persistence operation marks the case confirmed, records the confirmation timestamp, updates `profiles.active_birth_time`, mirrors it to legacy `profiles.birth_time`, sets `birth_time_status='confirmed'`, and returns `state="ready"`. `reported_birth_time` is never changed.

Medium and low results can be saved as candidates but cannot update either active-time field.

## API Events

The authenticated free journey route adds:

- `submit_life_events { caseId, events }`;
- `save_candidate { caseId, resultId }`;
- `confirm_candidate { caseId, resultId, time }`.

The response adds `lifeEvents` and `candidateResult`. Zod schemas reject unknown fields and client-supplied scores, confidence, candidate boundaries, active times, or application flags.

Scoring is idempotent for the same normalized events and algorithm version. A repeated request returns the stored result or recomputes the same result; it never creates a second confirmation.

## Persistence

Add to `birth_time_rectification_cases`:

- `life_events jsonb`;
- `candidate_result jsonb`;
- `event_scoring_version text`;
- `candidate_result_id uuid`;
- `candidate_saved_at timestamptz`.

The case `status` constraint is extended with `confirming`. Existing `candidate_start`, `candidate_end`, `confirmed_time`, and `confirmed_at` remain authoritative scalar mirrors. Service-role code owns candidate results and confirmation fields; authenticated browser clients receive read access only and cannot write scores or confirmation metadata directly.

## UI Flow

After the last questionnaire answer:

1. Replace the completed question list with a life-event card without requiring a page reload.
2. Show three rows initially. Each row has a domain selector, precision selector, and matching year/month/date control. Permit up to six rows.
3. Explain that dates are used only by the deterministic comparison engine and that unsupported precision is not invented.
4. Submit once to the free journey API and show an in-card scoring state.
5. Render the candidate interval, confidence, event count, domain count, and concise rule-based evidence summary returned by the server.
6. For low confidence, keep event editing visible. For medium confidence, show “保存候选范围” and “补充事件”. For high confidence, show a separate confirmation card that clearly distinguishes reported time, candidate interval, and the exact representative time proposed for active charting.
7. Enter the existing onboarding/consultation path only after the confirmation response returns `ready` with `activeTime`.

All controls follow `frontend/DESIGN.md`, remain keyboard operable, use persistent labels, and keep 44px touch targets. Status and error changes use live regions.

## Error Handling

- Invalid or insufficient events: return a field-level 400/409 response and keep the prior snapshot.
- Candidate calculation failure: persist no new score, keep `canApply=false`, and allow retry.
- Missing mandatory layers: return a low-confidence abstention with explicit missing-layer IDs.
- Persistence failure: do not advance the visible journey or update the profile.
- Stale confirmation: return 409 and the current snapshot.
- Duplicate confirmation: return the already-confirmed ready snapshot without changing the reported time.

## Testing and Acceptance

- Domain tests prove the final questionnaire answer transitions to `life_events` and never directly to confirmation.
- Python tests prove real candidate segments are ranked, ties abstain, missing layers cap confidence, date precision weights are fixed, and every score exposes rule IDs.
- Service tests prove event accumulation, owner scoping, idempotent scoring, stale confirmation rejection, and profile application only after valid confirmation.
- Route/client tests reject client-supplied score, confidence, candidate, and application fields.
- SQL contract tests prove event/result columns, RLS, and confirmation write restrictions.
- UI contract tests prove the form appears automatically after the last question and action sets match low/medium/high outcomes.
- Existing TypeScript, Python, lint, and production build gates remain green.
- Real-browser QA covers 375px, 768px, and 1280px widths and drives questionnaire completion, event validation, candidate presentation, and confirmation using a deterministic test fixture.

## Honesty Boundary

This feature supplies a reproducible local rectification score, not proof of a historically exact birth minute. The UI must use “候选时间” and “当前排盘使用时间”, never “真实出生时间” or “已验证的准确分钟”. External-oracle parity and real-case calibration remain separate confidence ceilings for any later product claim about empirical accuracy.
