import { NextResponse } from "next/server";
import {
  payloadFromProfile,
  type BirthRectificationProfile,
} from "@/lib/birth-rectification-payload";

const jyotishApiBase = process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200";

async function fetchQuestionnaire(payload: Record<string, unknown>) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 2500);
  try {
    const response = await fetch(`${jyotishApiBase}/api/active_rectification_questions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`jyotish_api_${response.status}`);
    return await response.json() as Record<string, unknown>;
  } finally {
    clearTimeout(timeout);
  }
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null) as { profile?: BirthRectificationProfile } | null;
  const payload = await payloadFromProfile(body?.profile ?? {}).catch(() => null);
  if (!payload) {
    return NextResponse.json({
      status: "blocked",
      boundary: "not_auto_rectified",
      reason: "profile_incomplete",
    });
  }
  const questionnaire = await fetchQuestionnaire(payload).catch(() => null);
  const candidateScan = questionnaire?.candidate_scan && typeof questionnaire.candidate_scan === "object"
    ? questionnaire.candidate_scan
    : null;
  const questions = Array.isArray(questionnaire?.questions) ? questionnaire.questions : [];
  return NextResponse.json({
    status: questionnaire ? "ok" : "blocked",
    candidate_scan: candidateScan,
    question_count: questions.length,
    boundary: "not_auto_rectified",
    source: questionnaire ? "active_rectification_questions" : "fallback_unavailable",
  });
}
