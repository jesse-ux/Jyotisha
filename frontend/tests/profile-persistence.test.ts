import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("upserts a missing profile when saving account details", () => {
  const source = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  assert.match(source, /fetch\("\/api\/account",[\s\S]*?\{[\s\S]*?method:\s*"PATCH"/);
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

test("account route persists the birth-time declaration before assessment", () => {
  // Given: the birthday step submits a reported time and its source metadata.
  const source = readFileSync(new URL("../src/app/api/account/route.ts", import.meta.url), "utf8");
  const patchContract = readFileSync(new URL("../src/lib/account-profile-patch.ts", import.meta.url), "utf8");
  const declarationColumns = [
    "reported_birth_time",
    "birth_time_source",
    "birth_time_period",
    "birth_time_clue",
    "uncertainty_before_minutes",
    "uncertainty_after_minutes",
  ] as const;

  // When: /api/account builds the profile upsert.
  // Then: every declaration field must cross the route boundary instead of being dropped.
  for (const column of declarationColumns) {
    assert.match(
      source,
      new RegExp(`payload\\.${column}\\s*!==\\s*undefined[\\s\\S]{0,160}${column}:\\s*payload\\.${column}`),
      `${column} is not persisted`,
    );
  }
  assert.match(source, /accountProfilePatchSchema\.safeParse/);
  assert.match(patchContract, /birthTimeSourceSchema\s*=\s*z\.enum\(\[[\s\S]*"legacy_import"/);
});

test("service role can insert and read birth-time declaration columns during profile upsert", () => {
  // Given: onboarding creates the profile before the birthday declaration is known.
  const migration = readFileSync(
    new URL(
      "../supabase/migrations/20260718103000_profile_birth_time_declaration_grants.sql",
      import.meta.url,
    ),
    "utf8",
  );

  // When: the existing profile is upserted after the birthday step.
  // Then: PostgREST may insert and read all declaration columns used by that upsert.
  assert.match(migration, /grant\s+insert\s*\([\s\S]*reported_birth_time[\s\S]*birth_time_source[\s\S]*uncertainty_after_minutes[\s\S]*\)\s*on\s+table\s+public\.profiles\s+to\s+service_role/i);
  assert.match(migration, /grant\s+select\s*\([\s\S]*reported_birth_time[\s\S]*birth_time_source[\s\S]*uncertainty_after_minutes[\s\S]*\)\s*on\s+table\s+public\.profiles\s+to\s+service_role/i);
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
    /grant\s+select\s*\(\s*district_code\s*,\s*updated_at\s*\)\s*on\s+table\s+public\.profiles\s+to\s+service_role/i,
  );
});
