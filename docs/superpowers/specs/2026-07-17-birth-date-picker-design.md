# Birth Date Picker Design

## Goal

Replace the browser-native birth-date input in `BirthTimeIntakeFields` with the shadcn Date Picker composition supplied by the user. Preserve the existing `YYYY-MM-DD` draft value and all birth-time journey behavior.

## Component structure

- Use the shadcn Base UI composition: `Popover`, `PopoverTrigger render={<Button />}`, `PopoverContent`, and a single-select `Calendar`.
- Add the shadcn `Calendar` and `Popover` primitives under `src/components/ui/`; reuse the existing `Button`, `cn`, Lucide icon system, and project tokens.
- Keep birth-date-specific value conversion and constraints in a focused `BirthDatePicker` component. `BirthTimeIntakeFields` continues to receive and emit `BirthTimeDraftPatch` values.

## Interaction

- The closed trigger has the same 44px minimum height and warm outline surface as existing inputs.
- Empty state reads `选择出生日期`; selected state displays a Chinese long date such as `1993年4月17日`.
- The calendar uses Chinese locale, single-date selection, month and year dropdowns, and years ordered newest first.
- Available dates run from `1900-01-01` through the user's current local date. Future dates and dates before 1900 are unavailable.
- Selecting a date writes the same local calendar date as `YYYY-MM-DD` and closes the popover.
- Reopening the picker shows the selected month. An empty picker opens within the allowed range rather than on an invalid future month.
- A confirmed birth-time profile disables the trigger exactly as the current native input does.

## Date handling

- Parse and format calendar dates in local calendar time; do not construct birth dates through UTC ISO parsing, which can shift a day in some time zones.
- An empty string maps to no selected date. The picker never emits a partial or invalid date string.
- The backend payload and database column remain unchanged.

## Accessibility

- Give the trigger an explicit accessible name associated with the visible `出生日期` label.
- Retain keyboard access through the shadcn/Base UI popover and React DayPicker calendar semantics.
- Preserve visible focus rings, disabled semantics, 44px targets, and collision-safe popover positioning.

## Styling

- Follow `frontend/DESIGN.md`: warm canvas, strong hairline, deep-brown focus/action color, `--radius-md`, and the existing elevated popover shadow.
- Calendar cells remain compact but provide at least a 44px interactive target on touch layouts.
- Do not introduce raw colors, new visual language, gradients, or browser-native date controls.

## Verification

- Contract test proves the native `type="date"` control is gone and the shadcn Date Picker composition is present.
- Date conversion tests cover empty, valid, leap-day, and local-timezone-safe round trips.
- Browser QA verifies opening, year/month navigation, selecting a date, automatic dismissal, disabled future dates, the confirmed disabled state, keyboard focus, and 375px/768px/1280px layouts.
- Run TypeScript, the existing test suite, lint, and a production build.
