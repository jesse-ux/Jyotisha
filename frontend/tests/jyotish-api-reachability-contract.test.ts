import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const root = new URL("../../", import.meta.url);
const readRoot = (path: string) => readFileSync(new URL(path, root), "utf8");
const mastra = readRoot("frontend/src/mastra/index.ts");
const rectification = readRoot("frontend/src/lib/birth-time-journey-engine-model.ts");
const synastry = readRoot("frontend/src/app/api/synastry/route.ts");
const apiServer = readRoot("scripts/jyotish_api_server.py");

test("commercial Jyotish paths resolve to a registered Python handler", () => {
  for (const path of [
    "/api/consultation_workflow",
    "/api/active_rectification_questions",
    "/api/active_rectification_score",
    "/api/active_rectification_events",
    "/api/varga_full",
    "/api/synastry",
  ]) {
    assert.match(apiServer, new RegExp(`['\"]${path.replaceAll("/", "\\/")}['\"]`));
  }
  assert.match(mastra, /\/api\/consultation_workflow/);
  assert.match(rectification, /\/api\/active_rectification_questions/);
  assert.match(rectification, /\/api\/active_rectification_score/);
  assert.match(rectification, /\/api\/active_rectification_events/);
  assert.match(synastry, /\/api\/varga_full/);
  assert.match(synastry, /\/api\/synastry/);
});
