# Question policy

## Agent-directed focus

In V8, the dossier and read-only tools expose facts, constraints, and candidate-contrast observations. The Director decides which evidence direction is most useful and writes the question. The server must not rotate through a fixed domain list, rank domains with hand-authored recall/privacy weights, require domain keywords, or turn test transcripts and example events into production scripts.

Candidate contrast may identify discriminating technique layers and all supported missing event kinds. Treat these as observations the Agent can weigh against the complete event ledger, recent conversation, refusals, privacy, and expected value. They are not a server-selected question and must not be copied mechanically into public wording.

Legacy semantic opportunities remain readable for compatibility and deterministic target clarification. Their `fallbackPrompt` is a failure-recovery surface, not the normal V8 topic selector. A no-target fallback must stay domain-neutral; a targeted fallback may ask only the server-known missing fact for that event.

### New-event questions

- Ask whether one relevant event exists; do not imply the user must have experienced a particular category.
- The Agent may use its own natural recall cues when useful, but examples are non-exhaustive and never server-required keywords.
- Do not invent an age, life stage, year, month, date range, or relative time window. A time or age may appear only when it already comes from accepted user evidence or another server-owned fact.
- Compare a proposed direction with the complete event ledger so the next question does not paraphrase an event already supplied.
- A missing domain alone is not a reason to ask about it. If no safe, useful question remains, stop with low confidence.

## One-turn rule

- Ask one question only.
- Prefer the concrete event the user just mentioned.
- A targeted question must include a valid text anchor for that event and must not switch targets.
- Do not ask a list of questions or combine a clarification with a new-domain request.
- Do not invent an event or date.
- Do not expose IDs, fields, scores, tools, models, or technique traces.
- Reject canned realizations such as `承接……请再说一件……`; a deterministic fallback must still read as one short contextual question.
- Validate the question semantically rather than by fixed phrases. For a follow-up about an already accepted event, natural wording must not be rejected only because it omits a token such as `哪次` or `哪件`; a new-event question must still satisfy the existence form above.

## Renderer validation and fallback trace

- Analysis history must make each Renderer path auditable after persistence and reload: model question accepted by validation, model question rejected by validation, or server deterministic fallback used.
- Record only safe categorical provenance, including the validation outcome, whether server fallback was used, and a bounded reason category such as model unavailable, model failure, or question rejected. Do not store the raw model prompt, rejected prose, hidden reasoning, private scores, or user event text in the trace.
- A Renderer rejection followed by a successful fallback is not equivalent to a model-rendered success. Preserve both facts in the same turn's analysis receipt.
- The deterministic fallback must remain server-owned and must obey the same existence, recall-cue, non-assumption, anti-invention, and semantic-overlap rules as a model realization.

## Target disposition

Respect the reconciled target state:

- `resolved`: close the target.
- `unknown`: close it; do not create an unparsed-event pending item for the refusal phrase.
- `declined`: close it and do not proactively return to that event or sensitive category.
- `direction_change`: close it and choose another useful opportunity.
- `answered_other_event`: save the new event without overwriting the old target; allow at most one gentle follow-up to the old target.
- `unresolved`: one follow-up is allowed only when the user has not refused or changed direction.
- `not_applicable`: no old target is being resolved.

The same `targetEventId` may be followed up consecutively at most once. A second answer about another event closes the old target instead of creating a loop.

## Date precision

- `day`: complete; never ask for finer detail.
- `month`: complete by default. Ask for a day or narrower stage only when diagnostics exist and either `winnerRetentionRate < 0.65` or `candidateClusterRetentionRate < 0.65`.
- `quarter`: a month may be requested.
- `year`: request a month or approximate range only when useful.
- `range`: refine only when it is broad and diagnostics show candidate-ranking impact.

Before enough events exist to score candidates, a month-dated event should lead to another important dated event, not a request for the exact day.

## Privacy and stopping

Health, death, illness, family, and relationship questions carry higher privacy cost. Once the user declines a category in the current Case, do not ask it again unless the user raises it. If no opportunity has enough value, stop with low confidence rather than running a longer questionnaire.
