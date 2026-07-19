import assert from "node:assert/strict";
import test from "node:test";
import { guidedTurnIdentity } from "../src/lib/birth-time-guided-turn-identity.ts";

test("persisted questions receive stable identities without leaking prior input", () => {
  assert.equal(guidedTurnIdentity(3, "education_entry"), "3:education_entry");
  assert.notEqual(
    guidedTurnIdentity(3, "education_entry"),
    guidedTurnIdentity(4, "relationship_entry"),
  );
});
