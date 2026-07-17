import assert from "node:assert/strict";
import test from "node:test";
import { runCreditRpc } from "../src/lib/consultation-billing.ts";

test("returns a valid business rejection without retrying it as an RPC error", async () => {
  // Given
  let calls = 0;
  const accounting = {
    async rpc() {
      calls += 1;
      return {
        data: [{ success: false, credits: 0, error_code: "insufficient_credits" }],
        error: null,
      };
    },
  };

  // When
  const result = await runCreditRpc(
    accounting,
    "begin_consultation_credit",
    "00000000-0000-4000-8000-000000000001",
    "00000000-0000-4000-8000-000000000002",
  );

  // Then
  assert.equal(calls, 1);
  assert.deepEqual(result, {
    success: false,
    credits: 0,
    error_code: "insufficient_credits",
  });
});

test("returns request_completed so the cancel route can respond with 409", async () => {
  const accounting = {
    async rpc() {
      return {
        data: { success: false, credits: 4, error_code: "request_completed" },
        error: null,
      };
    },
  };

  const result = await runCreditRpc(
    accounting,
    "cancel_consultation_credit",
    "00000000-0000-4000-8000-000000000001",
    "00000000-0000-4000-8000-000000000003",
  );

  assert.equal(result.success, false);
  assert.equal(result.error_code, "request_completed");
});
