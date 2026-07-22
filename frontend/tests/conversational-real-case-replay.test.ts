import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { resolve } from "node:path";
import { extractLifeEventEvidence } from "../src/lib/conversational-rectification/evidence-extractor.ts";

type ReplayManifest = {
  readonly cases: readonly {
    readonly case_id: string;
    readonly disclosure_order: readonly {
      readonly event_id: string;
      readonly user_utterance: string;
      readonly expected_extraction: {
        readonly date_value: string | null;
        readonly date_precision: "day" | "month" | "year" | "unknown";
        readonly domain: string;
        readonly scoreable: boolean;
      };
    }[];
  }[];
};

const manifestPath = resolve(
  process.cwd(),
  "../references/real_case_calibration/conversational_rectification_development_v1.json",
);
const manifest = JSON.parse(readFileSync(manifestPath, "utf8")) as ReplayManifest;

for (const replayCase of manifest.cases) {
  for (const [index, disclosure] of replayCase.disclosure_order.entries()) {
    test(`extracts public replay utterance ${replayCase.case_id}/${disclosure.event_id}`, () => {
      const evidence = extractLifeEventEvidence({
        rawText: disclosure.user_utterance,
        sourceTurnId: `00000000-0000-4000-8000-${String(index + 1).padStart(12, "0")}`,
        asOfDate: "2026-07-22",
      });

      assert.equal(evidence.length, 1);
      assert.equal(evidence[0]?.dateValue, disclosure.expected_extraction.date_value);
      assert.equal(evidence[0]?.datePrecision, disclosure.expected_extraction.date_precision);
      assert.equal(evidence[0]?.domain, disclosure.expected_extraction.domain);
      assert.equal(evidence[0]?.scoreable, disclosure.expected_extraction.scoreable);
    });
  }
}
