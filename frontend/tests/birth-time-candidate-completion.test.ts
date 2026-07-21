import assert from "node:assert/strict";
import test from "node:test";
import { candidateWorkingTime } from "../src/lib/birth-time-candidate-completion.ts";

test("unconfirmed candidate results cannot directly become the active consultation time", () => {
  assert.equal(candidateWorkingTime({}, {
    userId: "07e583fc-90b9-4fcb-a9d3-8de654eeac9a",
    caseId: "5425f9e7-3d45-491d-aab3-24cfd4261d51",
    resultId: "d9133ba2-afcf-56da-b40b-ace3d7124a7d",
    time: "04:53",
  }), null);
});
