# Minute Rectification P0: Input Evidence Contract

## Goal

Make a candidate-minute calculation reproducible across the local scanner and
the three-engine receipt without changing scoring weights or confirmation rules.

## Scope

- Canonicalize birth input with Lahiri and mean-node defaults.
- Hash the canonical input for every scanned candidate minute.
- Publish the required `-5`, `-2`, `-1`, `+1`, `+2`, and `+5` minute
  stability probes as pending evidence, not as a confidence result.
- Correct the public Steve Jobs comparison defaults to the canonical San
  Francisco coordinates.
- Preserve raw evidence hashes and add a separate semantic hash for known
  order-insensitive aspect lists.

## Non-goals

- No new questionnaire format, scoring weights, or candidate confirmation path.
- No claim that a candidate is accurate to the minute.
- No raw birth input or external raw response exposed to the browser.

## Acceptance

- Equivalent input mappings have the same canonical hash.
- Every candidate row carries a distinct input fingerprint when the minute
  differs.
- Stability probes are explicit and always state that minute confirmation is
  blocked pending public blind holdout evidence.
- The public comparison defaults match the canonical Steve Jobs source.
