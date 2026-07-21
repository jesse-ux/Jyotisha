import { NextResponse } from "next/server";
import {
  conversationalRectificationCreationPolicyFromEnvironment,
  conversationalRectificationDeploymentShaFromEnvironment,
} from "../../../lib/conversational-rectification/creation-policy.ts";

type Check = {
  status: "ok" | "degraded" | "blocked";
  message?: string;
  latencyMs?: number;
};

const jyotishApiBase = process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200";

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
  const gitCommit = conversationalRectificationDeploymentShaFromEnvironment();
  const rectificationV3MigrationsReady =
    process.env.RECTIFICATION_V3_MIGRATIONS_READY?.trim().toLowerCase() === "true";
  const creationPolicy = conversationalRectificationCreationPolicyFromEnvironment();
  const checks = {
    web: { status: "ok" } satisfies Check,
    supabasePublicConfig: envCheck(["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"]),
    supabaseServiceRole: envCheck(["SUPABASE_SERVICE_ROLE_KEY"]),
    modelProvider: anyEnvCheck(["LLM_MODELS_JSON", "OPENAI_API_KEY", "LLM_API_KEY", "DEEPSEEK_API_KEY"]),
    jyotishApi: await jyotishApiCheck(),
  };
  const status = aggregate(checks);
  const rectificationV3Ready = status === "ok"
    && creationPolicy.audience === "public";
  return NextResponse.json(
    {
      status,
      timestamp: new Date().toISOString(),
      deployment: {
        gitCommit,
      },
      rollout: {
        conversationalRectificationV3: {
          protocol: "conversational-evidence-v3",
          newCaseCreation: creationPolicy.audience === "paused" ? "paused" : "enabled",
          creationAudience: creationPolicy.audience,
          migrations: rectificationV3MigrationsReady ? "ready" : "unverified",
          syntheticSmoke: creationPolicy.smokeMatchesDeployment ? "matched" : "pending",
          readyForNewCases: rectificationV3Ready,
        },
      },
      checks,
    },
    { status: status === "ok" ? 200 : 503 },
  );
}
