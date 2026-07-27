import { NextResponse } from "next/server";
import { rectificationV4Context, rectificationV4Error, routeId } from "../../_server";

export const runtime = "nodejs";

export async function GET(_request: Request, { params }: { params: Promise<{ caseId: string }> }) {
  try {
    const context = await rectificationV4Context();
    const result = await context.service.loadCase(context.userId, routeId((await params).caseId));
    return result ? NextResponse.json(result) : NextResponse.json({ error: "没有找到这次生时校正记录。" }, { status: 404 });
  } catch (error) {
    return rectificationV4Error(error);
  }
}
