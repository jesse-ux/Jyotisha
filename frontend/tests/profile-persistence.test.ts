import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("upserts a missing profile when saving account details", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  assert.match(source, /fetch\("\/api\/account",\s*\{\s*method:\s*"PATCH"/s);
  assert.match(source, /credentials:\s*"same-origin"/);
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

test("service role can read every column used by account profile upserts", () => {
  // Given: the least-privilege grant omitted two columns submitted by /api/account.
  const migration = readFileSync(
    new URL(
      "../supabase/migrations/20260718080000_profiles_service_role_account_upsert_selects.sql",
      import.meta.url,
    ),
    "utf8",
  );

  // When: the corrective migration defines the account-upsert read grant.
  // Then: PostgREST can read both submitted columns while resolving existing rows.
  assert.match(
    migration,
    /grant\s+select\s*\(\s*district_code\s*,\s*updated_at\s*\)\s*on\s+table\s+public\.profiles\s+to\s+service_role/is,
  );
});
