import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const migration = readFileSync(
  new URL("../supabase/migrations/20260718104000_chart_profiles_upsert_id_grant.sql", import.meta.url),
  "utf8",
);

test("authenticated chart-profile upserts may update their unchanged conflict id", () => {
  assert.match(
    migration,
    /grant\s+update\s*\(\s*id\s*,\s*role\s*,\s*profile\s*,\s*updated_at\s*\)\s+on\s+table\s+public\.chart_profiles\s+to\s+authenticated/i,
  );
});
