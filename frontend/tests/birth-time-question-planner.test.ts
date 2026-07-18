import assert from "node:assert/strict";
import test from "node:test";
import { planEvidenceQuestion } from "../src/lib/birth-time-question-planner.ts";

test("planner chooses the unasked domain with the largest candidate split", () => {
  const question = planEvidenceQuestion({
    phase: "baseline",
    samples: [
      { d4Sign: "Aries", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
      { d4Sign: "Taurus", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
      { d4Sign: "Gemini", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
    ],
    askedDomains: [],
    coveredDomains: [],
    adaptiveRound: 0,
  });
  assert.equal(question?.domain, "relocation");
  assert.equal(question?.phase, "baseline");
});

test("planner never repeats a domain and returns null after canonical domains are exhausted", () => {
  assert.equal(planEvidenceQuestion({
    phase: "baseline",
    samples: [],
    askedDomains: ["education", "relocation", "relationship", "career", "health_pressure"],
    coveredDomains: [],
    adaptiveRound: 0,
  }), null);
});

test("planner prefers an uncovered domain when candidate splits tie", () => {
  const question = planEvidenceQuestion({
    phase: "baseline",
    samples: [
      { d4Sign: "Aries", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
      { d4Sign: "Aries", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
    ],
    askedDomains: [],
    coveredDomains: ["education"],
    adaptiveRound: 0,
  });
  assert.equal(question?.domain, "relocation");
});

test("planner resolves equal splits by canonical evidence-domain order", () => {
  const question = planEvidenceQuestion({
    phase: "adaptive",
    samples: [
      { d4Sign: "Aries", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
      { d4Sign: "Taurus", d9Sign: "Leo", d10Sign: "Virgo", d24Sign: "Cancer", d30Sign: "Libra" },
    ],
    askedDomains: [],
    coveredDomains: [],
    adaptiveRound: 1,
  });
  assert.equal(question?.domain, "education");
});

test("planner excludes asked domains before ranking remaining candidates", () => {
  const question = planEvidenceQuestion({
    phase: "baseline",
    samples: [
      { d4Sign: "Aries", d9Sign: "Cancer", d10Sign: "Leo", d24Sign: "Gemini", d30Sign: "Virgo" },
      { d4Sign: "Taurus", d9Sign: "Cancer", d10Sign: "Virgo", d24Sign: "Gemini", d30Sign: "Virgo" },
      { d4Sign: "Gemini", d9Sign: "Cancer", d10Sign: "Libra", d24Sign: "Gemini", d30Sign: "Virgo" },
    ],
    askedDomains: ["education", "relocation"],
    coveredDomains: [],
    adaptiveRound: 0,
  });
  assert.equal(question?.domain, "career");
});
