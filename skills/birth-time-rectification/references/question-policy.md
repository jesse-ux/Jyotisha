# Question policy

## Semantic opportunities

Question opportunities describe meaning, not final prose. New opportunities use `semantic-question-v2` and carry a goal, requested fields, anchors, context facts, forbidden moves, a natural fallback prompt, utility inputs, target event, and active state. Historical opportunities with only `prompt` remain readable by normalizing that text to `fallbackPrompt`.

The builder produces several candidates and publishes at most five active opportunities. Rank them by evidence and context: expected information gain, candidate-split relevance, date sensitivity, domain coverage, recent user topics, recall ease, novelty, repetition penalty, and privacy cost. Never select the first missing domain from a fixed education/relocation/relationship/career/finance/health sequence.

## One-turn rule

- Ask one question only.
- Prefer the concrete event the user just mentioned.
- A targeted question must include a valid text anchor for that event and must not switch targets.
- Do not ask a list of questions or combine a clarification with a new-domain request.
- Do not invent an event or date.
- Do not expose IDs, fields, scores, tools, models, or technique traces.

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
