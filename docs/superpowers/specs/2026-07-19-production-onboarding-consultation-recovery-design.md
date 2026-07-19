# Production Onboarding and Consultation Recovery Design

## Goal

Make the already-computed birth-time result enter conversation reliably, make the homepage timing starter reach a legal Jyotish workflow, and recover personalized starter content when its first Agent request exceeds the browser's initial wait.

## Confirmed runtime failures

- Production still contains the old low-result completion guard, which rejects `present_low_result` while the case status is `rectifying`.
- The homepage `timing` theme is sent into a Python report-theme boundary that accepts only `career`, `marriage`, `wealth`, `health`, and `spirituality`.
- Personalized onboarding completed and cached after roughly 19 seconds, while the browser aborted after 12 seconds and permanently suppressed another request until reload.

## Design

### Birth-time completion

Ship the existing narrow compatibility change. `present_low_result` accepts only `rectifying`; medium and saved results remain candidate-only. Case ownership, result ID, action ID, and representative-time guards remain mandatory.

### Consultation workflow projection

Add one typed projection at the Web-to-Python boundary. Public themes remain `career`, `marriage`, `wealth`, `timing`, and `general`. The projection sends:

- `timing` as report theme `career`, with a private `应期` prefix so Python selects its timing route;
- `general` as the existing `career`, `marriage`, and `wealth` report set;
- domain themes unchanged.

The user's visible question and stored transcript remain unchanged.

### Personalized onboarding recovery

Move onboarding response parsing and recovery into a focused client module. The first request keeps the current 12-second limit. If it times out, the page immediately exposes the existing safe default cards and continues in the background. A response marked `pending` is not treated as final personalized content; the client waits and retries the cache. A later `agent` or `cache` response replaces the temporary defaults and clears the unavailable note.

Authentication failures still redirect to login. Permanent HTTP or schema failures still expose the safe fallback note. Component styling, breakpoints, and copy hierarchy do not change.

## Testing

- A pure contract test proves `timing` produces a legal report theme and a private timing-routing question while other themes preserve their existing mapping.
- A client recovery test reproduces timeout → pending → cache and proves that the final personalized content wins without reload.
- Existing birth-time completion tests remain the regression gate for the production 409.
- The full frontend suite, lint, production build, and real-browser mobile/desktop flow must pass before deployment.

## Release

No Supabase migration is required. Merge the feature branch into `main`, push `main`, wait for the production workflow, then verify the public deployment identity, new CTA, personalized starter recovery, and a real timing starter request.
