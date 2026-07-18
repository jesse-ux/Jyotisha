# Birth Time Journey Design

## Goal

Turn the first-use birth-time question into one continuous journey: the assistant explains and guides, while deterministic code owns state transitions, time-quality assessment, candidate scanning, routing, and whether a time may become the active chart time.

## Delivery Scope

This delivery connects the web onboarding flow to the repository's existing candidate-time scanner. It includes:

- five explicit birth-time knowledge levels from the first time question;
- separate reported and active birth times;
- deterministic direct-chart versus rectification routing;
- a free rectification intake path that does not use `/api/consult` billing;
- candidate scanning with latitude, longitude, timezone, Lahiri ayanamsa, and the local domain engine;
- high-information choice questions and persisted answers;
- a hard application gate that refuses unsupported minute-level certainty.

The existing Python scorer only ranks coarse candidate clusters. It does not prove an exact minute against dated life events. Therefore this delivery may save rectification evidence and candidate ranges, but it must keep `can_apply=false` for scored questionnaire results. A hospital-record time may become active only when the deterministic ±2-minute sensitivity scan is stable.

## Responsibilities

### BirthTimeJourney

`advanceBirthTimeJourney(event, context) -> JourneySnapshot` is the only module allowed to choose the next state or route.

It owns:

- validation of source-specific inputs;
- uncertainty ranges;
- state transitions;
- stable-scan interpretation;
- `direct_chart`, `rectification`, or `pending` routing;
- `can_apply` decisions.

It does not generate prose, call a language model, persist data, or calculate a chart.

### Journey API

`POST /api/birth-time-journey` authenticates the user, parses the event, loads the user's profile/case, calls the deterministic module, calls the existing Python scan/score endpoints when required, and persists the returned snapshot.

The route is free. It must never reserve consultation credits.

### Birth Intake UI

The UI renders the input contract returned by the journey and uses fixed, user-facing Chinese copy for `assistant_intent`. It never chooses a route from chat text.

The existing `onboardingAgent` remains responsible only for the welcome message and starter questions after birth intake is complete. The normal `jyotishAgent` remains unavailable until an active birth time exists.

## State Model

States are:

- `collect_date`
- `collect_time_confidence`
- `collect_reported_time`
- `collect_location`
- `assessing`
- `rectifying`
- `candidate`
- `ready`

Routes are `pending`, `direct_chart`, and `rectification`.

Birth-time sources are:

- `hospital_record`
- `family_exact`
- `approximate`
- `period_only`
- `unknown`

Source rules:

| Source | Required input | Deterministic uncertainty | Route |
| --- | --- | --- | --- |
| Hospital record | exact time | ±2 minutes | stable scan → direct; sensitive/error → rectification |
| Family exact | exact time and 5/10/15-minute uncertainty | selected range | rectification |
| Approximate | center time and 15/30/60-minute uncertainty | selected range | rectification |
| Period only | morning/forenoon/afternoon/evening/late night | predefined range | rectification, no exact-time application |
| Unknown | optional family clue | whole-day unresolved | rectification, no exact-time application |

## Persistence

`profiles.birth_time` remains as a compatibility mirror of `active_birth_time` for existing calculation code.

New profile fields:

- `reported_birth_time`
- `active_birth_time`
- `birth_time_source`
- `birth_time_period`
- `uncertainty_before_minutes`
- `uncertainty_after_minutes`
- `birth_time_status`
- `rectification_confidence`
- `rectification_case_id`

`birth_time_rectification_cases` stores the questionnaire, answers, candidate scan, scoring result, algorithm settings, status, and confirmation metadata. Row-level security restricts every operation to the owning user. Raw reported time is never overwritten when active time changes.

Existing profiles with `birth_time` are backfilled as reported and active times with `birth_time_status='confirmed'` and `birth_time_source='legacy_import'`, so existing users are not forced through onboarding again.

## API Events

The first version accepts two events:

- `assess`: evaluate the stored birth-time declaration after location is known;
- `answer_question`: add or replace one A/B/C/D answer and recompute deterministic cluster scoring.

The response is a `JourneySnapshot` containing:

- `state`
- `assistantIntent`
- `input`
- `route`
- `confidence`
- `canApply`
- `reportedRange`
- `questionnaire`
- `scoring`

Unknown fields, invalid choices, missing authentication, and missing profile inputs are rejected at the HTTP boundary. Scanner failure safely routes to rectification and never silently activates the reported time.

## UI Flow

1. Ask the user's name.
2. Ask the birth date and show the five time-confidence choices.
3. Reveal only the time, uncertainty, period, or clue fields required by that choice.
4. Ask for birth location.
5. Show an assessment status card while the deterministic route runs.
6. If stable hospital data is accepted, continue to the existing starter questions.
7. Otherwise show the first three rectification questions, progress, current range, and the explicit note that no exact minute has been applied.

The account sheet uses the same birth-time fields, so later edits preserve the same contract.

## Error Handling

- Scanner unavailable: persist `rectifying`, show a retry-safe explanation, keep `can_apply=false`.
- Invalid source-specific input: keep the current collection state and show a field-level message.
- Persistence failure: return an error and do not advance the visible journey.
- Score endpoint failure: keep prior answers and prior snapshot; do not fabricate a result.
- Old profile: use the migration backfill and compatibility read path.

## Verification

- Unit tests cover every source route, stable/sensitive hospital scans, and the application gate.
- Route/service tests cover scanner payloads, failure fallback, and answer accumulation.
- SQL contract tests cover constraints, RLS, grants, and immutable reported-time semantics.
- Existing frontend, lint, TypeScript, build, and relevant Python rectification tests remain green.
- Manual QA runs the new first-use journey in the real Next.js page and observes both direct and rectification presentations without charging credits.
