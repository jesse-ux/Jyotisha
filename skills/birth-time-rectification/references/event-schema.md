# Event schema

Preserve the event's subject, related person, domain, event kind, original user wording, declared date text, normalized date range, precision, extraction status, correction lineage, source Turn, and scoreability.

These source fields are provenance for audit and replay only. Raw wording, source Turn, extraction path, and revision lineage must never add points, change technique weights, or act as a confidence multiplier. Scoring uses only the validated scoreable event contract and the server-owned contribution rules.

## Subject and scoreability

- A user's own supported event may be `scoreable`.
- A partner relationship event is scoreable only when the server policy explicitly permits it.
- Family events, bereavement, illness of relatives, and other third-party events are `context_only` by default.
- Do not classify a family health or death event as the user's own health event.
- A newly supplied event must not overwrite the event currently being clarified.

## Date precision

Keep `day`, `month`, `quarter`, `year`, `range`, and unresolved precision honestly. Never invent a day to complete a month, or a month/year from common sense. Month precision is sufficient by default; finer detail requires a server date-sensitivity reason.

Relative phrases such as “后来”, “第二年”, or “那时候” may be resolved only by the existing server context-date parser. If that parser cannot resolve them reliably, keep the evidence pending or contextual rather than guessing.

## Extraction boundary

Run deterministic extraction first. Model assistance is allowed only for deterministic `event_unparsed`, `pending_review`, or unsupported results. Its output is limited to a source span, summary, domain, event kind, subject, related person, and date text.

- `sourceSpan` and `dateText` must be continuous substrings of the user's answer.
- The model cannot provide normalized start/end dates.
- Server date parsing and schema validation remain authoritative.
- Invalid, timed-out, or invented model output is rejected and the deterministic pending result remains.
- The extraction agent receives no candidate ranges, scores, database write access, or profile mutation authority.

The raw answer remains in the Turn even when the user skips, declines, changes direction, or the event cannot be scored.
