# Task 2 — Deterministic Candidate Opportunities and Choice Scoring

## Implementation

- Added the versioned `birth-time-choice-scoring-v2` engine for reusable minute candidates, bounded life-stage windows, candidate-backed partitions, normalized information gain, and deterministic choice adjudication.
- Reused the existing local chart, D4/D9/D10/D24/D30, Vimshottari, and Narayana calculation path. Each candidate chart is computed once for the complete synthetic window set, then its activation rows are reused across dimensions.
- Persisted candidate models are strictly rebound to birth date, `as_of_date`, range, canonical candidate minutes, supported dimensions, bounded window dates, finite non-boolean activation values, and mandatory-layer shape before reuse.
- Fingerprint inputs contain only the scoring version, dimension code, ISO window boundaries, and sorted candidate memberships. User-facing prose never enters a hash basis.
- Added deterministic high/medium/low gates. Only high confidence can set `can_apply=true`; low and medium remain non-applicable. Public evidence is always empty and compatibility counts mirror effective answers/dimensions.
- Unknown, unmatched, free-text, client `option_id`, duplicate questions, empty server identifiers, unsupported dimensions, out-of-range candidate keys, negative/non-finite scores, and more than 10 effective evidence rows are rejected before scoring.
- Added strict legacy-safe POST routing for `/api/dynamic_rectification_opportunities` and `/api/dynamic_rectification_score`; existing active-rectification endpoints and their behavior were not changed.

## Files changed

- `scripts/dynamic_rectification.py`
- `scripts/dynamic_rectification_opportunities.py`
- `scripts/jyotish_api_server.py`
- `tests/test_dynamic_rectification.py`
- `tests/test_dynamic_rectification_scoring.py`
- `tests/test_active_rectification_api.py`
- `.superpowers/sdd/task-2-report.md`

## RED

1. `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m pytest -q tests/test_dynamic_rectification.py -k packet`
   - Collection failed as expected with `ImportError: cannot import name 'dynamic_rectification' from 'scripts'`.
2. `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m pytest -q tests/test_dynamic_rectification.py -k 'primary_choice or unknown or high_confidence'`
   - Three tests failed as expected because `score_choice_evidence` and `adjudicate_choice_rows` did not exist.
3. `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m pytest -q tests/test_active_rectification_api.py -k dynamic`
   - Four tests failed as expected because both dynamic API handler methods did not exist.
4. Candidate-model hardening regressions failed before their fixes: out-of-bounds windows and boolean activations were accepted, unmatched text was silently ignored, and semantically identical score maps were rejected when JSON key order differed.
5. The candidate reuse regression showed a missing D10 layer incorrectly blocking every dimension instead of career only.
6. The persisted-clock edge regression produced an invalid window ending before it began on the exact twelfth birthday; the under-age regression also showed unnecessary chart computation before age 12.
7. Final strict-boundary self-review reproduced acceptance of a negative candidate score and an empty persisted partition ID; both are now rejected before score accumulation.

## GREEN

1. `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m pytest -q tests/test_dynamic_rectification.py tests/test_active_rectification_api.py tests/test_active_rectification_questions.py tests/test_active_rectification_events.py`
   - `38` passed, `0` failed.
2. `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m ruff check scripts/dynamic_rectification.py tests/test_dynamic_rectification.py tests/test_active_rectification_api.py`
   - Passed with no diagnostics.
3. `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m compileall -q scripts/dynamic_rectification.py scripts/jyotish_api_server.py`
   - Passed.
4. `git diff --check`
   - Passed with no whitespace errors.
5. Real local-engine smoke using persisted `as_of_date=2026-07-18`, range `05:30—05:31`
   - Built version `birth-time-choice-scoring-v2`, `2` candidate minutes, and `20` bounded dimension/window activation rows. It correctly returned no opportunity when those two real candidates had no scoreable partition gain.

## Pre-work gate

- Ran `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45`.
- The gate remained red only on the unrelated fragment-governance assertion: `candidate_count` expected `0`, observed `2`. Remote visibility was also reported as blocked, so no cloud-sync claim is made.

## Self-review

- Candidate generation owns one versioned deterministic rectification boundary and delegates chart/Dasha mathematics to the existing engine rather than duplicating it.
- Untrusted HTTP payloads are allowlisted at the API boundary; persisted candidate models and service-resolved evidence are parsed again at the deterministic module boundary before expensive computation or scoring.
- Candidate-model reuse is deterministic across days because every window derives from persisted `as_of_date`; the process clock is never read.
- Effective evidence is the only scored input. Answered-count/UI semantics remain outside the scorer, so unknown and unmatched choices cannot become score evidence.
- Hash bases were manually inspected and contain no descriptors, labels, prompts, notes, or other prose.
- Legacy endpoints remain byte-for-byte unchanged except for adjacent registration of the two new routes; the full legacy focused suites stayed green.
- No dependencies, logging, mutable module state, broad exception handlers, or model-controlled confidence fields were introduced.

## Concerns

- Full-file Ruff on `scripts/jyotish_api_server.py` still reports inherited baseline debt (import ordering, legacy f-strings, an existing undefined `swe`, and other unrelated diagnostics). Ruff is clean for the new module and both modified test files; compileall and all focused suites pass.

## Review fixes

- Both dynamic routes now fail closed unless `JYOTISH_DYNAMIC_RECTIFICATION_TOKEN` is configured and the request carries its exact bearer value. Comparison uses `secrets.compare_digest`; missing and wrong credentials are rejected before payload validation or scoring.
- Removed both routes from `API_COMMAND_MAP`, `TECHNIQUE_EXAMPLE_ENDPOINTS`, technique-example dispatch, and generated technique summaries. They remain direct authenticated POST routes only.
- Latitude, longitude, and timezone are required. The normalized location triple is persisted inside the candidate model and exact-matched during reuse.
- Adjudication preserves submitted candidate order, so an overnight `23:59` to `00:00` leader is one contiguous segment.
- Question IDs are trimmed opaque nonempty strings. Duplicate detection uses the normalized value and remains enforced.
- Split candidate-model/opportunity work into `dynamic_rectification_opportunities.py` and scoring regressions into `test_dynamic_rectification_scoring.py` without changing public entrypoints.
- Pure LOC after the split: public engine `215`, opportunity module `231`, opportunity tests `168`, scoring/auth tests `213`, active API tests `230`.

### Review RED

1. Location/timezone reuse tests initially passed for the wrong reason because the old model rejected the new location field entirely; the original same-location reuse regression also failed until location became part of the canonical model contract.
2. Overnight and opaque-ID regressions failed with UUID validation; the independent reviewer reproduction also showed wall-clock sorting split `23:59` and `00:00` into tied leaders.
3. Missing/wrong bearer regressions reached request validation/scoring instead of raising `Forbidden`; a forged unauthenticated four-row request could therefore reach the scorer.
4. Missing `lat`, `lon`, or `tz` silently normalized to zero.
5. Browser-runnable registration assertions failed because both private endpoints appeared in technique examples, command mapping, dispatch, and summaries.

### Review GREEN

1. `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m pytest -q tests/test_dynamic_rectification.py tests/test_dynamic_rectification_scoring.py tests/test_active_rectification_api.py tests/test_active_rectification_questions.py tests/test_active_rectification_events.py`
   - `45` passed, `0` failed.
2. `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m ruff check scripts/dynamic_rectification.py scripts/dynamic_rectification_opportunities.py tests/test_dynamic_rectification.py tests/test_dynamic_rectification_scoring.py tests/test_active_rectification_api.py`
   - Passed with no diagnostics after correcting one import-order finding.
3. `/Users/jesse/Downloads/Copse/astrology/yinduzhanxing/.venv/bin/python -m compileall -q scripts/dynamic_rectification.py scripts/dynamic_rectification_opportunities.py scripts/jyotish_api_server.py`
   - Passed.
4. `git diff --check`
   - Passed after removing one trailing blank line in the API regression file.
