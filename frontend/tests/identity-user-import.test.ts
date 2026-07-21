import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  applyIdentityUsers,
  normalizeSupabaseUsers,
} from "../scripts/import-supabase-auth-users.mjs";

const fixturePath = fileURLToPath(
  new URL("./fixtures/supabase-auth-users.json", import.meta.url),
);
const scriptPath = fileURLToPath(
  new URL("../scripts/import-supabase-auth-users.mjs", import.meta.url),
);

test("Supabase user transform preserves portable identity fields only", () => {
  const source = JSON.parse(readFileSync(fixturePath, "utf8"));
  const users = normalizeSupabaseUsers(source);

  assert.deepEqual(users, [
    {
      id: "018f4e6d-7a11-7000-8000-000000000001",
      email: "person@example.com",
      emailVerified: true,
      emailVerifiedAt: new Date("2026-07-01T01:02:03.000Z"),
      name: "Person One",
      image: "https://example.com/person.png",
      createdAt: new Date("2026-06-01T01:02:03.000Z"),
      updatedAt: new Date("2026-07-02T01:02:03.000Z"),
    },
    {
      id: "018f4e6d-7a11-7000-8000-000000000002",
      email: "second@example.com",
      emailVerified: false,
      emailVerifiedAt: null,
      name: "second",
      image: null,
      createdAt: new Date("2026-06-02T01:02:03.000Z"),
      updatedAt: new Date("2026-06-02T01:02:03.000Z"),
    },
  ]);
  const serialized = JSON.stringify(users);
  assert.doesNotMatch(
    serialized,
    /encrypted_password|last_sign_in_at|raw_user_meta_data|must-not-be-imported/,
  );
});

test("Supabase user transform aborts duplicate canonical emails", () => {
  const source = JSON.parse(readFileSync(fixturePath, "utf8"));
  source.push({
    ...source[1],
    id: "018f4e6d-7a11-7000-8000-000000000003",
    email: " SECOND@example.com ",
  });

  assert.throws(
    () => normalizeSupabaseUsers(source),
    new Error("source contains duplicate canonical emails"),
  );
});

test("identity user apply is transactional, parameterized, and rerunnable", async () => {
  const users = normalizeSupabaseUsers(
    JSON.parse(readFileSync(fixturePath, "utf8")),
  );
  const calls: Array<{ text: string; values?: unknown[] }> = [];
  const client = {
    async query(text: string, values?: unknown[]) {
      calls.push({ text, values });
      return { rowCount: 1 };
    },
  };

  await applyIdentityUsers(client, users);
  await applyIdentityUsers(client, users);

  assert.equal(calls.filter((call) => call.text === "BEGIN").length, 2);
  assert.equal(calls.filter((call) => call.text === "COMMIT").length, 2);
  const upserts = calls.filter((call) => /insert into identity\.users/.test(call.text));
  assert.equal(upserts.length, 4);
  assert.ok(upserts.every((call) => /on conflict \(id\) do update/.test(call.text)));
  assert.ok(upserts.every((call) => /\$1/.test(call.text)));
  assert.ok(upserts.every((call) => !call.text.includes("person@example.com")));
});

test("CLI defaults to a redacted dry-run without a database URL", () => {
  const env = { ...process.env };
  delete env.IDENTITY_DATABASE_URL;
  const result = spawnSync(process.execPath, [scriptPath, fixturePath], {
    encoding: "utf8",
    env,
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /"mode":"dry-run"/);
  assert.match(result.stdout, /"users":2/);
  assert.doesNotMatch(result.stdout, /person@example\.com|second@example\.com/);
});

test("CLI apply mode requires an identity database URL without printing inputs", () => {
  const env = { ...process.env };
  delete env.IDENTITY_DATABASE_URL;
  const result = spawnSync(
    process.execPath,
    [scriptPath, fixturePath, "--apply"],
    { encoding: "utf8", env },
  );

  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /IDENTITY_DATABASE_URL is required for --apply/);
  assert.doesNotMatch(result.stderr, /person@example\.com|must-not-be-imported/);
});
