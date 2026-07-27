import { setTimeout as sleep } from "node:timers/promises";
import { createRectificationV4CandidateEngine } from "../src/lib/rectification-v4/candidate-engine.ts";
import { createRectificationV4SupabaseStore } from "../src/lib/rectification-v4/supabase-store.ts";
import { authorRectificationV4Question } from "../src/lib/rectification-v4/question-author.ts";
import { createRectificationV4Worker } from "../src/lib/rectification-v4/worker.ts";
import { createAdminSupabaseClient } from "../src/lib/supabase/admin-client-core.ts";

const intervalMs = Number(process.env.RECTIFICATION_V4_WORKER_POLL_MS ?? "1000");
const once = process.argv.includes("--once");
let stopped = false;
for (const signal of ["SIGINT", "SIGTERM"] as const) process.once(signal, () => { stopped = true; });

const worker = createRectificationV4Worker({
  store: createRectificationV4SupabaseStore(createAdminSupabaseClient()),
  engine: createRectificationV4CandidateEngine({
    apiBase: process.env.JYOTISH_API_BASE ?? "http://127.0.0.1:5200",
  }),
  questionAuthor: authorRectificationV4Question,
});

do {
  const worked = await worker.runOnce();
  if (once) break;
  if (!worked) await sleep(Number.isFinite(intervalMs) && intervalMs >= 100 ? intervalMs : 1000);
} while (!stopped);
