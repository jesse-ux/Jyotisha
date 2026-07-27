import { NextResponse } from "next/server";
import { acceptRangeRequestSchema } from "@/lib/rectification-v4/contracts";
import { rectificationV4Context, rectificationV4Error, requestBody, routeId } from "../../../_server";

export const runtime = "nodejs";

export async function POST(request: Request, { params }: { params: Promise<{ caseId: string }> }) {
  try {
    const body = await requestBody(request, acceptRangeRequestSchema);
    const context = await rectificationV4Context();
    const result = await context.service.acceptRange({
      ...body,
      userId: context.userId,
      caseId: routeId((await params).caseId),
    });
    return result
      ? NextResponse.json(result)
      : NextResponse.json({ error: "当前结果还不足以保存这个范围。" }, { status: 409 });
  } catch (error) {
    return rectificationV4Error(error);
  }
}
