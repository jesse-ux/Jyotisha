import { NextResponse } from "next/server";
import { answerRequestSchema } from "@/lib/rectification-v4/contracts";
import { rectificationV4Context, rectificationV4Error, requestBody, routeId } from "../../../_server";

export const runtime = "nodejs";

export async function POST(request: Request, { params }: { params: Promise<{ caseId: string }> }) {
  try {
    const body = await requestBody(request, answerRequestSchema);
    const context = await rectificationV4Context();
    const result = await context.service.answer({ ...body, userId: context.userId, caseId: routeId((await params).caseId) });
    return result
      ? NextResponse.json(result, { status: 202 })
      : NextResponse.json({ error: "当前没有待回答的问题，请刷新后重试。" }, { status: 409 });
  } catch (error) {
    return rectificationV4Error(error);
  }
}
