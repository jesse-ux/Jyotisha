import assert from "node:assert/strict"
import { existsSync, readFileSync } from "node:fs"
import test from "node:test"

const packageJson = readFileSync(new URL("../package.json", import.meta.url), "utf8")

test("provides the shadcn calendar and popover primitives", () => {
  assert.equal(existsSync(new URL("../src/components/ui/calendar.tsx", import.meta.url)), true)
  assert.equal(existsSync(new URL("../src/components/ui/popover.tsx", import.meta.url)), true)
  assert.match(packageJson, /"react-day-picker"/)
})
