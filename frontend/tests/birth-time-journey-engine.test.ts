import assert from "node:assert/strict";
import test from "node:test";
import { eventScorePayload } from "../src/lib/birth-time-journey-engine-model.ts";

test("journey engine serializes only stored event-scoring inputs", () => {
  const payload = eventScorePayload({
    birthDate: "1993-04-17",
    startTime: "14:00",
    endTime: "15:00",
    lat: 31.2304,
    lon: 121.4737,
    tz: 8,
    events: [
      { id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", domain: "career", date: "2019-07", precision: "month" },
      { id: "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea", domain: "education", date: "2011", precision: "year" },
      { id: "0ef52e51-ab5f-453b-81e5-adb44a929224", domain: "relationship", date: "2021-05-01", precision: "day" },
    ],
  });

  assert.deepEqual(payload, {
    birth_date: "1993-04-17",
    start_time: "14:00",
    end_time: "15:00",
    lat: 31.2304,
    lon: 121.4737,
    tz: 8,
    events: [
      { id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5", domain: "career", date: "2019-07", precision: "month" },
      { id: "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea", domain: "education", date: "2011", precision: "year" },
      { id: "0ef52e51-ab5f-453b-81e5-adb44a929224", domain: "relationship", date: "2021-05-01", precision: "day" },
    ],
  });
  assert.equal("confidence" in payload, false);
  assert.equal("can_apply" in payload, false);
});
