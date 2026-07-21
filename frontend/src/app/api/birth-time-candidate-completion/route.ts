import { NextResponse } from "next/server";
import { z } from "zod";

export const runtime = "nodejs";

const requestSchema = z.object({
  caseId: z.string().uuid(),
  resultId: z.string().uuid(),
  time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
}).strict();

/** Compatibility endpoint for stale clients; unconfirmed candidates never write profiles. */
export async function POST(request: Request) {
  const parsed = requestSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return NextResponse.json({ error: "候选时间格式不正确" }, { status: 400 });
  return NextResponse.json(
    { error: "候选时间不能直接采用", message: "候选范围已保留；请补充资料，或在高置信结果出现后通过正式确认继续。" },
    { status: 409 },
  );
}
