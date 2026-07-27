import { NextResponse } from "next/server";
import { rectificationV4Context, rectificationV4Error, routeId } from "../../_server";

export const runtime = "nodejs";

export async function GET(_request: Request, { params }: { params: Promise<{ jobId: string }> }) {
  try {
    const context = await rectificationV4Context();
    const job = await context.service.loadJob(context.userId, routeId((await params).jobId));
    return job ? NextResponse.json({ job }) : NextResponse.json({ error: "没有找到这次处理任务。" }, { status: 404 });
  } catch (error) {
    return rectificationV4Error(error);
  }
}
