import { NextResponse } from "next/server";

import { getTruthSourceRuntimeIdentity } from "@/lib/truth-source-runtime-identity";

type Check = {
  status: "ok" | "degraded" | "blocked";
  message?: string;
  latencyMs?: number;
};

const jyotishApiBase = process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200";
const gitCommit =
  process.env.GITHUB_SHA
  ?? process.env.VERCEL_GIT_COMMIT_SHA
  ?? process.env.NEXT_PUBLIC_GIT_COMMIT
  ?? "unknown";

function envCheck(names: string[]): Check {
  const missing = names.filter((name) => !process.env[name]);
  return missing.length
    ? { status: "blocked", message: `missing:${missing.join(",")}` }
    : { status: "ok" };
}

function anyEnvCheck(names: string[]): Check {
  return names.some((name) => process.env[name])
    ? { status: "ok" }
    : { status: "blocked", message: `missing_one_of:${names.join("|")}` };
}

async function jyotishApiCheck(): Promise<Check> {
  const started = Date.now();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3000);
  try {
    const response = await fetch(`${jyotishApiBase}/api/health`, {
      cache: "no-store",
      signal: controller.signal,
    });
    return {
      status: response.ok ? "ok" : "degraded",
      message: response.ok ? undefined : `http:${response.status}`,
      latencyMs: Date.now() - started,
    };
  } catch (error) {
    return {
      status: "blocked",
      message: error instanceof Error ? error.name : "jyotish_api_unavailable",
      latencyMs: Date.now() - started,
    };
  } finally {
    clearTimeout(timeout);
  }
}

function aggregate(checks: Record<string, Check>) {
  if (Object.values(checks).some((check) => check.status === "blocked")) return "blocked";
  if (Object.values(checks).some((check) => check.status === "degraded")) return "degraded";
  return "ok";
}

export async function GET() {
  const truthSourceIdentity = getTruthSourceRuntimeIdentity();
  const checks = {
    web: { status: "ok" } satisfies Check,
    supabasePublicConfig: envCheck(["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"]),
    supabaseServiceRole: envCheck(["SUPABASE_SERVICE_ROLE_KEY"]),
    modelProvider: anyEnvCheck(["LLM_MODELS_JSON", "OPENAI_API_KEY", "LLM_API_KEY", "DEEPSEEK_API_KEY"]),
    jyotishApi: await jyotishApiCheck(),
    researchTruthSource: {
      status: truthSourceIdentity.status,
      message: truthSourceIdentity.mountStatus === "mounted" ? undefined : truthSourceIdentity.mountStatus,
    } satisfies Check,
  };
  const status = aggregate(checks);
  return NextResponse.json(
    {
      status,
      timestamp: new Date().toISOString(),
      deployment: {
        gitCommit,
      },
      truthSource: truthSourceIdentity,
      checks,
    },
    { status: status === "ok" ? 200 : 503 },
  );
}
