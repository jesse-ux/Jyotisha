# Commercial onboarding UX → research contract — 2026-07-19

Purpose: reuse commercial UX strengths in the research repo without importing business runtime.

## Flow to learn

称呼 → 出生时间 → 出生地点 → 时间校正

Observed commercial strengths:

- conversational first contact instead of static form
- one question per step
- progressive disclosure: ask only the next missing datum
- birth-time uncertainty is accepted instead of forcing a fake exact time
- profile-missing guidance instead of generic failure
- 资料缺失时引导补全，不把缺失说成系统错误
- mobile-first chat layout
- starter questions after onboarding
- visible evidence-status language: based on chart evidence, not generic horoscope prose

## Research-safe abstraction

Target form: research interaction prototype.

Allowed:

- onboarding flow contract
- prompt/response transcript fixtures
- birth-time uncertainty UX notes
- evidence-status display notes
- mobile layout references
- tests that ensure missing data prompts are useful

Forbidden:

- 不迁移积分、支付、商业账户权益
- no Supabase service-role runtime
- no production authentication dependency
- no commercial redemption/admin-code logic

## Contract requirements

1. If name is missing, ask for name/nickname only.
2. If birth time is missing or uncertain, ask for known precision; do not force exact time.
3. If place is missing, ask for place after birth-time step.
4. If profile remains incomplete, explain the missing field and continue useful guidance where possible.
5. When chart evidence is available, label answers as evidence-based.
6. Do not hide claim boundaries behind a friendly UI.

## Next implementation target

Create a lightweight research prototype that can replay onboarding transcripts and show which evidence layers would become available after each step.
