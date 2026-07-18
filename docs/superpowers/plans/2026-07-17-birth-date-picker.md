# Birth Date Picker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the browser-native birth-date input with the user-supplied shadcn Popover + Calendar Date Picker while preserving the existing `YYYY-MM-DD` profile contract.

**Architecture:** Add the official shadcn Base Nova `Calendar` and `Popover` primitives, then compose them in a focused `BirthDatePicker` client component. Keep local-calendar parsing and serialization beside the existing birth-time draft model so every consumer receives the same date-only string without UTC shifts.

**Tech Stack:** Next.js 16, React 19, TypeScript, shadcn Base Nova, Base UI, React DayPicker, date-fns, Lucide, Node test runner.

## Global Constraints

- The closed control follows the exact shadcn composition supplied by the user: `PopoverTrigger render={<Button />}` plus `PopoverContent` containing a single-select `Calendar`.
- Date values remain `YYYY-MM-DD`; the API payload and database schema do not change.
- The selectable range is `1900-01-01` through the user's current local date; future dates are disabled.
- The calendar uses Chinese locale with month and year dropdowns, newest years first.
- Confirmed birth-time profiles keep the date trigger disabled.
- Use only existing `frontend/DESIGN.md` tokens and shadcn semantic tokens; add no raw colors.
- Preserve 44px targets, keyboard operation, focus visibility, and collision-safe popover positioning.

---

### Task 1: Date-only value adapter

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/src/lib/birth-time-intake-model.ts`
- Test: `frontend/tests/birth-time-intake.test.ts`

**Interfaces:**
- Produces: `parseBirthDate(value: string): Date | undefined`
- Produces: `formatBirthDate(value: Date): string`
- Consumes: date-fns `parse`, `format`, and `isValid`

- [ ] **Step 1: Add failing date-only behavior tests**

Extend the existing import and append these Given/When/Then tests:

```ts
import {
  assistantIntentCopy,
  birthTimePersistenceValues,
  describeBirthTimeDraft,
  formatBirthDate,
  isBirthTimeDraftReady,
  parseBirthDate,
  type BirthTimeDraft,
} from "../src/lib/birth-time-intake-model.ts";

test("birth date parsing preserves the local calendar day", () => {
  const parsed = parseBirthDate("1993-04-17");

  assert.equal(parsed?.getFullYear(), 1993);
  assert.equal(parsed?.getMonth(), 3);
  assert.equal(parsed?.getDate(), 17);
});

test("birth date values round trip leap days and reject invalid input", () => {
  const leapDay = parseBirthDate("2000-02-29");

  assert.equal(leapDay === undefined ? undefined : formatBirthDate(leapDay), "2000-02-29");
  assert.equal(parseBirthDate(""), undefined);
  assert.equal(parseBirthDate("2001-02-29"), undefined);
});
```

- [ ] **Step 2: Run the tests in a negative UTC offset and confirm red**

Run:

```bash
TZ=America/Los_Angeles node --test tests/birth-time-intake.test.ts
```

Expected: FAIL because `parseBirthDate` and `formatBirthDate` are not exported yet.

- [ ] **Step 3: Install date-fns as a direct dependency**

Run:

```bash
npm install date-fns
```

Expected: `package.json` and `package-lock.json` declare `date-fns` directly.

- [ ] **Step 4: Implement strict local-calendar parsing and formatting**

Add to `birth-time-intake-model.ts`:

```ts
import { format, isValid, parse } from "date-fns";

const birthDatePattern = "yyyy-MM-dd";

export function parseBirthDate(value: string): Date | undefined {
  if (value === "") return undefined;
  const parsed = parse(value, birthDatePattern, new Date(2000, 0, 1));
  if (!isValid(parsed) || format(parsed, birthDatePattern) !== value) return undefined;
  return parsed;
}

export function formatBirthDate(value: Date): string {
  return format(value, birthDatePattern);
}
```

- [ ] **Step 5: Run the adapter tests and confirm green**

Run:

```bash
TZ=America/Los_Angeles node --test tests/birth-time-intake.test.ts
```

Expected: all birth-time intake tests PASS.

- [ ] **Step 6: Commit the adapter**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/lib/birth-time-intake-model.ts frontend/tests/birth-time-intake.test.ts
git commit -m "feat: add birth date value adapter"
```

---

### Task 2: shadcn Calendar and Popover primitives

**Files:**
- Create: `frontend/src/components/ui/calendar.tsx`
- Create: `frontend/src/components/ui/popover.tsx`
- Create: `frontend/tests/birth-date-picker-contract.test.ts`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

**Interfaces:**
- Produces: `Calendar(props: React.ComponentProps<typeof DayPicker>)`
- Produces: `Popover`, `PopoverTrigger`, and `PopoverContent`
- Consumes: the existing `Button`, `buttonVariants`, `cn`, Lucide icons, and shadcn semantic CSS variables.

- [ ] **Step 1: Write the failing primitive contract test**

Create `tests/birth-date-picker-contract.test.ts`:

```ts
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const packageJson = readFileSync(new URL("../package.json", import.meta.url), "utf8");

test("provides the shadcn calendar and popover primitives", () => {
  assert.equal(existsSync(new URL("../src/components/ui/calendar.tsx", import.meta.url)), true);
  assert.equal(existsSync(new URL("../src/components/ui/popover.tsx", import.meta.url)), true);
  assert.match(packageJson, /"react-day-picker"/);
});
```

- [ ] **Step 2: Run the primitive contract and confirm red**

Run:

```bash
node --test tests/birth-date-picker-contract.test.ts
```

Expected: FAIL because the primitive files and direct dependency do not exist.

- [ ] **Step 3: Add the official Base Nova primitives**

Run from `frontend/`:

```bash
npx shadcn@latest add calendar popover --yes
```

Expected: shadcn reads the existing `components.json`, creates `src/components/ui/calendar.tsx` and `src/components/ui/popover.tsx`, reuses the existing `button.tsx`, and adds `react-day-picker` plus required direct dependencies without changing the project style preset.

- [ ] **Step 4: Review generated changes before accepting them**

Run:

```bash
git diff -- frontend/package.json frontend/package-lock.json frontend/src/components/ui/button.tsx frontend/src/components/ui/calendar.tsx frontend/src/components/ui/popover.tsx
```

Expected: no overwrite of the project's existing Button behavior; generated Calendar uses `react-day-picker`, and Popover uses the Base UI composition required by `style: base-nova`.

- [ ] **Step 5: Run the primitive contract and TypeScript**

Run:

```bash
node --test tests/birth-date-picker-contract.test.ts
npx tsc --noEmit
```

Expected: both commands PASS.

- [ ] **Step 6: Commit the primitives**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/components/ui/calendar.tsx frontend/src/components/ui/popover.tsx frontend/tests/birth-date-picker-contract.test.ts
git commit -m "feat: add shadcn calendar primitives"
```

---

### Task 3: BirthDatePicker composition and intake integration

**Files:**
- Create: `frontend/src/components/birth-date-picker.tsx`
- Modify: `frontend/src/components/birth-time-intake.tsx`
- Modify: `frontend/DESIGN.md`
- Test: `frontend/tests/birth-date-picker-contract.test.ts`

**Interfaces:**
- Consumes: `parseBirthDate(value: string)` and `formatBirthDate(value: Date)` from Task 1.
- Consumes: `Calendar`, `Popover`, `PopoverContent`, `PopoverTrigger`, `Button`, `CalendarIcon`, and `zhCN`.
- Produces: `BirthDatePicker({ value, disabled, onChange })` where `value` is `YYYY-MM-DD` and `onChange` receives `YYYY-MM-DD`.

- [ ] **Step 1: Document the Date Picker primitive before product code**

Extend `frontend/DESIGN.md` Section 5 with:

```md
### Birth date picker

- **Composition:** shadcn outline Button trigger, Base UI Popover, and a single-select React DayPicker Calendar.
- **Range:** local dates from 1900-01-01 through today; future dates are disabled. Month and year dropdowns provide direct navigation, with newest years first.
- **Value:** display Chinese long dates while emitting the existing `YYYY-MM-DD` profile value without UTC conversion.
- **States:** empty, open, selected, focus-visible, disabled confirmed profile, and unavailable date.
- **Accessibility:** visible label, explicit trigger naming, 44px targets, keyboard calendar navigation, focus return, and collision-safe popup positioning.
```

- [ ] **Step 2: Add a failing integration contract**

Append to `birth-date-picker-contract.test.ts`:

```ts
const intake = readFileSync(new URL("../src/components/birth-time-intake.tsx", import.meta.url), "utf8");
const pickerUrl = new URL("../src/components/birth-date-picker.tsx", import.meta.url);

test("replaces the native birth date input with the shadcn date picker", () => {
  assert.equal(existsSync(pickerUrl), true);
  assert.doesNotMatch(intake, /type="date"/);
  assert.match(intake, /<BirthDatePicker/);
  const picker = readFileSync(pickerUrl, "utf8");
  assert.match(picker, /<PopoverTrigger/);
  assert.match(picker, /render=\{<Button/);
  assert.match(picker, /<Calendar/);
  assert.match(picker, /captionLayout="dropdown"/);
  assert.match(picker, /startMonth=\{new Date\(1900, 0\)\}/);
  assert.match(picker, /reverseYears/);
});
```

- [ ] **Step 3: Run the integration contract and confirm red**

Run:

```bash
node --test tests/birth-date-picker-contract.test.ts
```

Expected: FAIL because `BirthDatePicker` is absent and the native date input remains.

- [ ] **Step 4: Implement the focused picker component**

Create `src/components/birth-date-picker.tsx` with this composition:

```tsx
"use client";

import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import { CalendarIcon } from "lucide-react";
import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { formatBirthDate, parseBirthDate } from "@/lib/birth-time-intake-model";

type BirthDatePickerProps = {
  readonly value: string;
  readonly disabled: boolean;
  readonly onChange: (value: string) => void;
};

export function BirthDatePicker({ value, disabled, onChange }: BirthDatePickerProps) {
  const labelId = useId();
  const valueId = useId();
  const [open, setOpen] = useState(false);
  const selected = parseBirthDate(value);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return (
    <div className="grid gap-2">
      <span id={labelId}>出生日期</span>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger
          render={
            <Button
              type="button"
              variant="outline"
              disabled={disabled}
              aria-labelledby={`${labelId} ${valueId}`}
              data-empty={selected === undefined}
              className="w-full justify-start px-3 text-left font-normal data-[empty=true]:text-muted-foreground"
            />
          }
        >
          <CalendarIcon aria-hidden="true" />
          <span id={valueId}>
            {selected === undefined
              ? "选择出生日期"
              : format(selected, "PPP", { locale: zhCN })}
          </span>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-auto p-0">
          <Calendar
            key={value || "empty"}
            mode="single"
            className="[--cell-size:2.75rem]"
            locale={zhCN}
            selected={selected}
            defaultMonth={selected ?? today}
            captionLayout="dropdown"
            navLayout="after"
            startMonth={new Date(1900, 0)}
            endMonth={today}
            reverseYears
            disabled={{ before: new Date(1900, 0, 1), after: today }}
            onSelect={(nextDate) => {
              if (nextDate === undefined) return;
              onChange(formatBirthDate(nextDate));
              setOpen(false);
            }}
          />
        </PopoverContent>
      </Popover>
    </div>
  );
}
```

- [ ] **Step 5: Replace the native input without changing the patch contract**

In `birth-time-intake.tsx`, import `BirthDatePicker` and replace the first `<label>...</label>` block with:

```tsx
<BirthDatePicker
  value={value.date}
  disabled={isConfirmed}
  onChange={(date) => onPatch({ date })}
/>
```

- [ ] **Step 6: Run targeted contracts and TypeScript**

Run:

```bash
node --test tests/birth-date-picker-contract.test.ts tests/birth-time-intake.test.ts
npx tsc --noEmit
```

Expected: all tests and TypeScript PASS.

- [ ] **Step 7: Commit the composition**

```bash
git add frontend/DESIGN.md frontend/src/components/birth-date-picker.tsx frontend/src/components/birth-time-intake.tsx frontend/tests/birth-date-picker-contract.test.ts
git commit -m "feat: replace native birth date input"
```

---

### Task 4: Real-surface QA and release gates

**Files:**
- Modify only if QA finds a defect in the files owned by Tasks 1–3.

**Interfaces:**
- Consumes: the complete BirthDatePicker flow.
- Produces: browser evidence for selection, dismissal, range constraints, disabled state, and responsive layout.

- [ ] **Step 1: Run the full automated gates**

```bash
npm test
npm run lint
npm run build
```

Expected: 100% test pass, zero lint errors, and a successful production build.

- [ ] **Step 2: Measure every modified TypeScript file**

```bash
for file in src/lib/birth-time-intake-model.ts src/components/ui/calendar.tsx src/components/ui/popover.tsx src/components/birth-date-picker.tsx src/components/birth-time-intake.tsx tests/birth-date-picker-contract.test.ts tests/birth-time-intake.test.ts; do
  awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(\/\/|#|--)/' "$file" | wc -l
done
```

Expected: each file is at or below 250 pure lines; no type escape hatch, parameter bloat, negative flag name, or unrelated helper is introduced.

- [ ] **Step 3: Verify the real interaction at 375px, 768px, and 1280px**

At each width, use the in-app browser to:

1. Open the birth date picker and confirm the popup stays inside the viewport.
2. Confirm Chinese month/year dropdowns and keyboard focus are visible.
3. Navigate to 1993, select April 17, and confirm the trigger displays `1993年4月17日`.
4. Confirm the popover closes and the controlled draft contains `1993-04-17`.
5. Reopen and confirm April 1993 remains selected.
6. Confirm dates after today and before 1900 are unavailable.
7. Load a confirmed profile and confirm the trigger cannot open.
8. Confirm no browser-native date chooser appears.

Expected: every scenario passes with 44px targets, no clipping, no horizontal overflow, and no console errors.

- [ ] **Step 4: Run the visual QA dual-oracle gate**

Provide fresh 375px, 768px, and 1280px evidence to two independent read-only reviewers. One reviews design-system fidelity and visual polish; the other reviews interaction, accessibility, and regression risk.

Expected: both reviewers return PASS. Fix any concrete issue and repeat only the affected evidence.

- [ ] **Step 5: Final diff hygiene**

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; unrelated pre-existing user changes remain untouched and are named in the handoff.
