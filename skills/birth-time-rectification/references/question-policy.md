# Question policy

## Semantic opportunities

Question opportunities describe meaning, not final prose. New opportunities use `semantic-question-v2` and carry a goal, requested fields, anchors, context facts, forbidden moves, a natural fallback prompt, utility inputs, target event, and active state. Historical opportunities with only `prompt` remain readable by normalizing that text to `fallbackPrompt`.

The builder produces several candidates and publishes at most five active opportunities. Rank them by evidence and context: expected information gain, candidate-split relevance, date sensitivity, domain coverage, recent user topics, recall ease, novelty, repetition penalty, and privacy cost. Never select the first missing domain from a fixed education/relocation/relationship/career/finance/health sequence.

Use the latest answer and latest accepted event as the current topic. Do not let keywords from older turns pull the conversation back to a stale domain, and do not give an uncovered domain both a coverage reward and a second topic reward from the same older event. Once the minimum domain coverage is already present, continuity and information gain should outweigh collecting another domain merely because it is missing.

### New-event existence and recall cues

- Ask whether a relevant event exists before asking for its details. Use an existence form such as “过去是否有过……” or “如果有……”, not a presuppositional form that implies the user must have had that event.
- Offer 2–5 concrete recall cues as non-exhaustive examples. Make it explicit that they are examples, allow any other relevant event, and allow the user to say that none occurred.
- Recall cues may name ordinary event types supported by the selected domain, but must not assert that any cue happened to this user.
- Do not invent an age, life stage, year, month, date range, or relative time window. A time or age may appear only when it already comes from accepted user evidence or another server-owned fact allowed by the opportunity contract.
- Compare every new-event opportunity with the latest accepted event even when their domain labels differ. If they overlap semantically in subject, action, transition, or outcome, apply a utility penalty before ranking. If the candidate is merely a cross-domain paraphrase of the latest event, suppress it instead of asking the same event again with different words.
- Domain coverage must not override semantic continuity or duplicate-event protection. A missing domain is not sufficient reason to ask a semantically overlapping question.

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
