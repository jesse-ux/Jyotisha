import assert from "node:assert/strict"
import { existsSync, readFileSync } from "node:fs"
import test from "node:test"

const packageJson = readFileSync(new URL("../package.json", import.meta.url), "utf8")
const intake = readFileSync(new URL("../src/components/birth-time-intake.tsx", import.meta.url), "utf8")
const pickerUrl = new URL("../src/components/birth-date-picker.tsx", import.meta.url)

test("provides the shadcn calendar and popover primitives", () => {
  assert.equal(existsSync(new URL("../src/components/ui/calendar.tsx", import.meta.url)), true)
  assert.equal(existsSync(new URL("../src/components/ui/popover.tsx", import.meta.url)), true)
  assert.match(packageJson, /"react-day-picker"/)
})

test("replaces the native birth date input with the shadcn date picker", () => {
  assert.equal(existsSync(pickerUrl), true)
  assert.doesNotMatch(intake, /type="date"/)
  assert.match(intake, /<BirthDatePicker/)
  const picker = readFileSync(pickerUrl, "utf8")
  assert.match(picker, /<PopoverTrigger/)
  assert.match(picker, /render=\{<Button/)
  assert.match(picker, /<Calendar/)
  assert.match(picker, /captionLayout="dropdown"/)
  assert.match(picker, /startMonth=\{new Date\(1900, 0\)\}/)
  assert.match(picker, /reverseYears/)
})

test("keeps the shadcn date-of-birth dropdown navigation order", () => {
  // Given the shadcn Date of Birth composition
  const picker = readFileSync(pickerUrl, "utf8")

  // When dropdown captions are enabled
  // Then the picker must not move the full-width nav after the caption selects
  assert.doesNotMatch(picker, /navLayout="after"/)
})

test("opens an empty birth date picker at 1997 instead of the current year", () => {
  // Given: a new user has not selected a birth date yet.
  const picker = readFileSync(pickerUrl, "utf8")

  // When: the popover chooses its initial visible month.
  // Then: it starts in 1997 so common birth years are nearby.
  assert.match(picker, /const emptyDefaultMonth = new Date\(1997, 0, 1\)/)
  assert.match(picker, /defaultMonth=\{selected \?\? emptyDefaultMonth\}/)
})
