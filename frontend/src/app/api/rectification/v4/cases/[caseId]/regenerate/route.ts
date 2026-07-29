import { NextResponse } from "next/server";
import { caseActionRequestSchema } from "@/lib/rectification-v4/contracts";
import { rectificationV4Context, rectificationV4Error, requestBody, routeId } from "../../../_server";

export const runtime = "nodejs";

export async function POST(request: Request, { params }: { params: Promise<{ caseId: string }> }) {
  try {
    const body = await requestBody(request, caseActionRequestSchema);
    const context = await rectificationV4Context();
    const result = await context.service.regenerateQuestion({
      ...body,
      userId: context.userId,
      caseId: routeId((await params).caseId),
    });
    return result
      ? NextResponse.json(result)
      : NextResponse.json({ error: "当前问题不能重新生成，请刷新后重试。" }, { status: 409 });
  } catch (error) {
    return rectificationV4Error(error);
  }
}
