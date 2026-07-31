import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const migration = readFileSync(new URL(
  "../supabase/migrations/20260731010000_rectification_case_resume_and_scoring_v2.sql",
  import.meta.url,
), "utf8");

test("scoring v2 migration only resumes an answerable or actively processing Case", () => {
  assert.match(migration, /v_case\.algorithm_version = p_algorithm_version/);
  assert.match(migration, /v_case\.status = 'awaiting_answer'[\s\S]*v_case\.current_question is not null/);
  assert.match(migration, /v_case\.status = 'processing'[\s\S]*birth_time_rectification_v4_jobs[\s\S]*status in \('pending', 'processing'\)/);
  assert.doesNotMatch(migration, /v_case\.status = 'paused'/);
});

test("scoring v2 migration retires incompatible unfinished work without touching profile birth time", () => {
  assert.match(migration, /algorithm_version <> 'rectification-v5-matrix-scoring-2'[\s\S]*accepted_range_start is null/);
  assert.match(migration, /set status = 'stale'/);
  assert.match(migration, /set status = 'abandoned', phase = 'complete', current_question = null/);
  assert.doesNotMatch(migration, /profiles\.active_birth_time|update\s+public\.profiles/i);
});

test("scoring v2 migration permits historical snapshots but defaults new artifacts to v2", () => {
  assert.match(migration, /alter column algorithm_version set default 'rectification-v5-matrix-scoring-2'/);
  assert.match(migration, /rectification-v4-range-scoring-1[\s\S]*rectification-v5-matrix-scoring-1[\s\S]*rectification-v5-matrix-scoring-2/);
});
