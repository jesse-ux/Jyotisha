import assert from "node:assert/strict";
import test from "node:test";

import { assertLedgerFilesPresent } from "../scripts/db-migrate.mjs";

const retiredFilename = "20260727010000_admin_users.sql";
const retiredChecksum =
  "785f4fdc65db1028623cc7b5a2571217b913ef9e55f5a17b01658a71612976de";

test("accepts the retired staging migration only with its reviewed checksum", () => {
  assert.doesNotThrow(() =>
    assertLedgerFilesPresent(new Map([[retiredFilename, retiredChecksum]]), []),
  );
});

test("rejects checksum drift for the retired staging migration", () => {
  assert.throws(
    () => assertLedgerFilesPresent(new Map([[retiredFilename, "0".repeat(64)]]), []),
    /migration checksum mismatch: 20260727010000_admin_users\.sql/,
  );
});

test("still rejects any undeclared missing migration", () => {
  assert.throws(
    () =>
      assertLedgerFilesPresent(
        new Map([["20260727020000_unknown.sql", "0".repeat(64)]]),
        [],
      ),
    /migration file missing: 20260727020000_unknown\.sql/,
  );
});
