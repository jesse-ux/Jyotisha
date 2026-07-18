# Account menu and task dialogs

Date: 2026-07-17

## 1. Goal

Replace the monolithic right-side account sheet with a lightweight account popover and focused dialogs. Opening the account menu must no longer interrupt the chat with an oversized panel containing every account action.

The design keeps the existing warm editorial visual language and existing backend behavior. It does not add email editing, a general settings page, or a chart library.

## 2. Entry points

### Sidebar account trigger

The account trigger at the lower-left of the sidebar opens an account popover anchored above the trigger. It does not open a modal or disable the entire chat surface.

### Credit trigger

The credit trigger in the upper-right of the chat header opens the redeem dialog directly. A user selecting their balance has a clear redemption intent and should not be routed through the account menu first.

### System-directed entry points

- Missing birth data opens the profile dialog directly.
- A zero-credit state or a consultation response with HTTP 402 opens the redeem dialog directly.
- These flows never open the account popover as an intermediate step.

## 3. Account popover

The popover is approximately 280px wide on desktop, with viewport collision protection. It uses the existing canvas color, warm hairline border, and restrained elevated shadow. It contains no nested cards.

Content order:

1. Identity header with avatar, display name, and account email. The email is informational and is not presented as editable.
2. `个人资料` menu item.
3. `兑换点数` menu item with the current balance aligned on the trailing edge.
4. `管理兑换码` menu item, rendered only for administrators.
5. A divider.
6. `退出登录` destructive menu item.

Each interactive row has a minimum 44px target. Hover uses the existing warm neutral selected surface. The action color is reserved for focus, selected state, and destructive emphasis rather than decorating every row.

Behavior:

- Clicking `个人资料` closes the popover and opens the profile dialog.
- Clicking `兑换点数` closes the popover and opens the redeem dialog.
- Clicking `管理兑换码` closes the popover and navigates in the same tab to `/admin/codes`.
- Clicking `退出登录` closes the popover and opens the logout confirmation dialog. It does not sign out immediately.
- Clicking outside or pressing Escape closes the popover.
- Closing the popover returns focus to the account trigger.

## 4. Profile dialog

The profile dialog is a centered modal with a desktop maximum width of approximately 560px and a viewport-safe maximum height. It replaces the profile portion of the old account sheet.

The dialog contains:

- Title: `个人资料`.
- Existing name field.
- Existing birth date and birth time fields.
- Existing country, province, city, and district fields.
- Existing save action.
- Inline validation, saving, success, and error states.

Saving does not close the dialog. A successful save updates the local profile state and displays the existing inline success message. Closing with unsaved edits discards the draft and restores the last saved profile the next time the dialog opens.

## 5. Redeem dialog

The redeem dialog is a centered modal with a desktop maximum width of approximately 420px.

The dialog contains:

- Title: `兑换点数`.
- Current balance displayed near the title or at the top of the form.
- Redemption-code input.
- Primary `兑换` action.
- Inline validation, submitting, success, and error states.

Successful redemption keeps the dialog open and updates all visible balance representations from the same account state: the dialog balance, chat-header credit trigger, and account-popover balance. The input is cleared after a successful redemption.

## 6. Logout confirmation dialog

The logout confirmation is a compact centered modal. It contains:

- Title: `退出登录？`
- Supporting text: `退出后，需要重新登录才能继续查看对话。`
- Secondary `取消` action.
- Destructive `确认退出` action.

`取消` closes the dialog and returns focus to the account trigger. `确认退出` starts sign-out, becomes disabled, and reads `正在退出`. A sign-out failure leaves the dialog open, restores the action, and shows a concise inline error.

## 7. Responsive behavior

- Desktop and tablet use an anchored account popover.
- On mobile, the popover remains a compact floating menu positioned within the viewport; it does not become a right-side sheet.
- All task dialogs use a centered viewport-safe surface with 16px minimum outer spacing and internal scrolling when content exceeds the available height.
- The profile dialog may occupy most of the mobile width, but retains the visual and semantic behavior of a dialog rather than becoming a persistent account page.

## 8. Motion and accessibility

- Popover entry: 120ms opacity plus 4px vertical translation.
- Dialog entry: 180ms opacity plus a small transform using the existing standard easing.
- Reduced-motion removes translation and retains only immediate or short opacity state changes.
- Only opacity, transform, and color animate.
- The popover trigger exposes `aria-expanded` and `aria-controls`.
- The popover uses menu semantics with keyboard-reachable items.
- Dialogs use `role="dialog"`, `aria-modal="true"`, a labelled title, focus trapping, and background inertness.
- Escape closes the topmost surface only.
- Closing a dialog returns focus to the element that opened it, including the upper-right credit trigger.

## 9. State and component boundaries

Replace the overloaded `profileOpen` and `redeemOpen` relationship with explicit surface state:

- `accountMenuOpen: boolean`
- `activeAccountDialog: "profile" | "redeem" | "logout" | null`

The UI is divided into four responsibilities:

- `AccountMenu`: identity and account-action routing only.
- `ProfileDialog`: profile draft, validation, and save interaction.
- `RedeemDialog`: balance display, redemption input, and redemption result.
- `LogoutDialog`: logout confirmation, pending state, and sign-out error.

Opening a dialog always closes the menu. At most one account surface is open. Existing persistence functions and API routes remain the source of truth; this change reorganizes presentation and entry routing rather than changing account data contracts.

The project design contract must replace the current `Account sheet` section in `frontend/DESIGN.md` with the new account popover and three task-dialog primitives before implementation styling is added.

## 10. Error handling

- Account-loading errors remain visible near the affected account surface without exposing raw provider or database errors.
- Profile save failure leaves the dialog open and preserves the user's draft.
- Redemption failure leaves the entered code in place for correction or retry.
- Navigation to the admin page uses the existing route guard as the authoritative authorization check; hiding the menu item is only a presentation rule.
- Sign-out failure restores the confirmation action and shows a concise inline error in the logout dialog.

## 11. Acceptance criteria

1. The sidebar account trigger opens a popover and never opens the former right-side account sheet.
2. The upper-right credit trigger opens the redeem dialog directly.
3. `个人资料` opens a profile-only dialog with the existing fields and save behavior.
4. `兑换点数` opens a redeem-only dialog and updates every displayed balance after success.
5. `管理兑换码` appears only to administrators and navigates to `/admin/codes`.
6. `退出登录` opens a confirmation dialog; only `确认退出` signs out, with a visible pending state.
7. Missing-profile and insufficient-credit flows open the correct task dialog directly.
8. Popover and dialogs support outside click where appropriate, Escape, focus return, keyboard navigation, and reduced motion.
9. No right-side account sheet markup, styling, or overloaded account-sheet state remains.
10. Existing profile persistence, redemption, admin authorization, onboarding, and consultation billing behavior continue to pass regression tests.

## 12. Verification plan

- Unit coverage for the surface-routing rules and the balance update contract where those rules are represented as pure logic.
- TypeScript, lint, existing frontend tests, and production build.
- Manual browser QA at 375px, 768px, and 1280px.
- Exercise account popover open/close, all three dialogs, logout cancel/confirm/failure, administrator visibility, successful and failed redemption, profile save failure, Escape, outside click, focus return, and reduced-motion behavior.
- Confirm no console errors or accessibility regressions on the changed states.
