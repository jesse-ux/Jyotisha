import assert from "node:assert/strict";
import test from "node:test";
import { reserveConsultationModel } from "../src/lib/consultation-model-selection.ts";

test("rejects an unknown model before credit reservation", async () => {
  let reservationCalls = 0;

  const result = await reserveConsultationModel(
    "removed-model",
    () => null,
    async () => {
      reservationCalls += 1;
      return { success: true };
    },
  );

  assert.deepEqual(result, { status: "unavailable" });
  assert.equal(reservationCalls, 0);
});

test("keeps the resolved agent model and ledger model id together", async () => {
  const model = { id: "deepseek-pro", model: "deepseek-v4-pro" };

  const result = await reserveConsultationModel(
    "deepseek-pro",
    (modelId) => modelId === model.id ? model : null,
    async () => ({ success: true, credits: 4 }),
  );

  assert.deepEqual(result, {
    status: "reserved",
    model,
    usageModelId: "deepseek-pro",
    reservation: { success: true, credits: 4 },
  });
});
