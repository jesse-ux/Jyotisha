import assert from "node:assert/strict";
import test from "node:test";

import { assertLedgerFilesPresent } from "../scripts/db-migrate.mjs";

const retiredMigrations = new Map([
  [
    "20260727010000_admin_users.sql",
    "785f4fdc65db1028623cc7b5a2571217b913ef9e55f5a17b01658a71612976de",
  ],
  [
    "20260727020000_epay_packages_orders.sql",
    "e922177b4d60d04ba9380b19badba1ffbe792304b1580f8748f7ad1b6e855e1b",
  ],
  [
    "20260727030000_payment_admin_stats.sql",
    "b71e46ca696d0ef2b74f239829f9f808dd910742e32d3e3f7dc641a1ad7e767d",
  ],
  [
    "20260729010000_epay_settings.sql",
    "dc3ed919b463e96b79473c19235dceb7cb491362b1f684db070aea80830cf6e9",
  ],
  [
    "20260730010000_admin_payment_permissions.sql",
    "1744437eb133f860930898fd1a33c07440d4a63ff22a8f34c0b5e3ddb286c177",
  ],
]);

test("accepts every retired staging migration only with its reviewed checksum", () => {
  assert.doesNotThrow(() => assertLedgerFilesPresent(retiredMigrations, []));
});

test("rejects checksum drift for a retired staging migration", () => {
  const drifted = new Map(retiredMigrations);
  drifted.set("20260727020000_epay_packages_orders.sql", "0".repeat(64));
  assert.throws(
    () => assertLedgerFilesPresent(drifted, []),
    /migration checksum mismatch: 20260727020000_epay_packages_orders\.sql/,
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
