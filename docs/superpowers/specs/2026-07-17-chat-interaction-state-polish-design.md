# Chat Interaction State Polish

## Goal

Make question suggestions, session navigation, the model selector, and the credit indicator behave predictably without changing chat billing or allowing concurrent sends.

## Approved behavior

- Initial question cards remain visible while a user types or selects a question. They disappear only when the first user message is submitted.
- Follow-up suggestions remain visible while a user types or selects one. The current set disappears when the next user message is submitted; the next assistant answer may provide a new set.
- Existing sessions remain selectable while another session has a pending request. The pending request continues against its original session, while all new sends remain globally locked until it settles.
- The model popover width is reduced from 360px to 180px, with viewport collision protection retained.
- The credit icon and number share the same visual center using the existing flex layout and a compact line box.

## Architecture

Keep the current session-scoped request routing and billing locks. Correct only the UI guards: suggestion visibility follows submitted message state rather than draft state, session navigation no longer inherits the send lock, and CSS uses existing design tokens for the two layout adjustments.

## Error and cancellation behavior

Cancellation remains unchanged. If a send is withdrawn before output and the optimistic user message is removed, the previous suggestion set can reappear with the restored draft.

## Verification

- Contract tests cover draft-independent initial and follow-up suggestions, unlocked session navigation, the 180px popover, and credit alignment.
- Run the full frontend test suite, TypeScript, ESLint, production build, and a local preview interaction check.
