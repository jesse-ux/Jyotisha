import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("upserts a missing profile when saving account details", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  assert.match(source, /fetch\("\/api\/account",\s*\{\s*method:\s*"PATCH"/s);
});

test("account route upserts profiles with the server admin client", () => {
  const source = readFileSync(new URL("../src/app/api/account/route.ts", import.meta.url), "utf8");
  assert.match(source, /createAdminSupabaseClient\(\)/);
  assert.match(source, /\.from\("profiles"\)\s*\.upsert\(/);
});

test("account route can fall back when coordinate columns are not deployed", () => {
  const source = readFileSync(new URL("../src/app/api/account/route.ts", import.meta.url), "utf8");
  assert.match(source, /withoutCoordinates/);
  assert.match(source, /PGRST204|42703|schema cache|column/i);
});
