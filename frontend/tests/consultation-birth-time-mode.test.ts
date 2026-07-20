import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  UNVERIFIED_BIRTH_TIME_NOTICE,
  applyBirthTimeModeToWorkflowContext,
  createBirthTimeModeOutputGuard,
  consultationBirthTimeModeSchema,
  serverProfileAllowsBirthTimeMode,
  shouldRunBirthChartWorkflow,
} from "../src/lib/consultation-birth-time-mode.ts";

test("general-no-birth-time is an explicit server mode that never runs a chart workflow", () => {
  assert.equal(consultationBirthTimeModeSchema.safeParse("verified_chart").success, true);
  assert.equal(consultationBirthTimeModeSchema.safeParse("unverified_birth_time").success, true);
  assert.equal(consultationBirthTimeModeSchema.safeParse("general_no_birth_time").success, true);
  assert.equal(shouldRunBirthChartWorkflow("general_no_birth_time"), false);
  assert.equal(shouldRunBirthChartWorkflow("verified_chart"), true);
});

test("unverified chart context can never become confirmed or retain precise timing permission", () => {
  const original = {
    success: true,
    consumer_context: {
      core_status: "ready",
      answer_policy: {
        can_answer_direction: true,
        can_answer_precise_timing: true,
      },
    },
  };
  const guarded = applyBirthTimeModeToWorkflowContext(original, "unverified_birth_time");

  assert.equal(original.consumer_context.answer_policy.can_answer_precise_timing, true);
  assert.deepEqual(guarded.consumer_context.answer_policy, {
    can_answer_direction: true,
    can_answer_precise_timing: false,
    birth_time_confidence: "unverified_reported_time",
    candidate_is_confirmed: false,
  });
});

test("server profile truth prevents a candidate or edited report from being submitted as confirmed", () => {
  const candidateProfile = {
    active_birth_time: "05:18",
    reported_birth_time: "06:10",
    birth_time_source: "approximate",
    birth_time_status: "candidate",
  };
  assert.equal(serverProfileAllowsBirthTimeMode(candidateProfile, "verified_chart", "05:18"), false);
  assert.equal(serverProfileAllowsBirthTimeMode(candidateProfile, "unverified_birth_time", "05:18"), false);
  assert.equal(serverProfileAllowsBirthTimeMode(candidateProfile, "unverified_birth_time", "06:10"), true);
  assert.equal(serverProfileAllowsBirthTimeMode(candidateProfile, "general_no_birth_time", null), true);

  const confirmedProfile = { ...candidateProfile, birth_time_status: "confirmed" };
  assert.equal(serverProfileAllowsBirthTimeMode(confirmedProfile, "verified_chart", "05:18"), true);
  assert.equal(serverProfileAllowsBirthTimeMode(confirmedProfile, "unverified_birth_time", "06:10"), false);
});

test("every unverified streamed answer receives a stable visible marker and timing guard", () => {
  const transform = createBirthTimeModeOutputGuard("unverified_birth_time", false);
  const first = transform("2026年8月适合观察方向。");
  const second = transform("你一定会升职。");

  assert.match(first, new RegExp(UNVERIFIED_BIRTH_TIME_NOTICE));
  assert.match(first, /具体时间已省略/);
  assert.doesNotMatch(second, /一定会升职/);
  assert.doesNotMatch(second, new RegExp(UNVERIFIED_BIRTH_TIME_NOTICE));
});

test("consult route validates mode before billing and general mode uses no chart agent or workflow", () => {
  const route = readFileSync(new URL("../src/app/api/consult/route.ts", import.meta.url), "utf8");
  const mastra = readFileSync(new URL("../src/mastra/index.ts", import.meta.url), "utf8");
  const parseIndex = route.indexOf("chatRequestSchema.safeParse");
  const profileTruthIndex = route.indexOf("serverProfileAllowsBirthTimeMode(", parseIndex);
  const reserveIndex = route.indexOf("reserveConsultationModel(", parseIndex);

  assert.ok(parseIndex >= 0 && profileTruthIndex > parseIndex && reserveIndex > profileTruthIndex);
  assert.match(route, /general_no_birth_time/);
  assert.match(route, /shouldRunBirthChartWorkflow/);
  assert.match(route, /getGeneralJyotishAgent/);
  assert.match(mastra, /getGeneralJyotishAgent/);
  assert.match(mastra, /Never calculate, infer, or claim a personal birth chart/);
  assert.match(mastra, /tools:\s*\{\}/);
});

test("homepage sends explicit modes and never routes an unverified minute through the retired questionnaire", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const route = readFileSync(new URL("../src/app/api/consult/route.ts", import.meta.url), "utf8");

  assert.match(page, /consultationMode:/);
  assert.match(page, /general_no_birth_time/);
  assert.match(page, /unverified_birth_time/);
  assert.doesNotMatch(page, /birthTimeStatus === "confirmed" \? "direct_chart" : "rectification"/);
  assert.match(route, /旧版生时校正入口已停用/);
  assert.ok(route.indexOf("旧版生时校正入口已停用") < route.indexOf("reserveConsultationModel(", route.indexOf("chatRequestSchema.safeParse")));
});
