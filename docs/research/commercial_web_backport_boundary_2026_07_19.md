# Research-to-commercial capability boundary — 2026-07-19

Purpose: keep the asset flow honest. Research repo is the personal core asset and source of astrological capability. Commercial repo productizes stable research contracts for users.

## Research capabilities that commercial may productize

| Capability | Research web status | Evidence |
|---|---|---|
| Daily starlanguage entry | local research UX exists | `jyotish-app/index.html#daily-guidance-card`; guarded by `tests/test_frontend_productization.py` |
| Birth-time rectification entry | local research UX exists | `jyotish-app/index.html#entry-rectification`; guarded by `tests/test_frontend_productization.py` |
| Local chart library | local research UX exists | `jyotish-app/index.html#saved-chart-panel`; `jyotish-app/main.js#saveCurrentChartToLibrary`; guarded by `tests/test_frontend_productization.py` |
| Display-name field | local research profile exists | `jyotish-app/index.html#profile-display-name`; `PROFILE_DISPLAY_NAME_KEY`; guarded by `tests/test_frontend_productization.py` |
| Chat history actions | local research sessions exist | rename/share/archive/delete in `jyotish-app/main.js`; guarded by `tests/test_frontend_productization.py` |

## Not equivalent by design

| Commercial capability | Research boundary |
|---|---|
| Supabase `/api/account` profile save | Research web is static/local-first; it must not claim cloud profile persistence. |
| `profiles` service-role upsert grants | Commercial database migration only; research repo may document it but should not require Supabase for local research web. |
| Cookie-authenticated account route | Commercial runtime only; research web stores display name locally. |
| Credits, billing, subscriptions | Commercial-only business layer; never part of research repo capability. |

## Claim rule

Research web may say:
- “research capability has a local UX/reference implementation”
- “profile display name and sessions persist in localStorage”
- “stable research contracts can be synced outward to commercial”

Research web must not say:
- “cloud profile persistence is equivalent to commercial”
- “Supabase account/profile upsert is available in the static research site”
- “research web and commercial web are 100% identical”
- “commercial credits, billing, subscriptions, or account entitlements are research capabilities”

## Current optimization priority

1. Improve real research capability first; sync stable contracts outward to commercial.
2. Keep timing claims exploratory until independent negative holdout labels exist.
3. Keep external oracle mismatch reports as attribution, not majority-vote truth.
4. Keep commercial account/payment/runtime details out of research repo except as deployment contract notes.
