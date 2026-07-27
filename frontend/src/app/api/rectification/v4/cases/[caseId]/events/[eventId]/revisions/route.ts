import { NextResponse } from "next/server";
import { reviseEventRequestSchema } from "@/lib/rectification-v4/contracts";
import { appendEventRevision } from "@/lib/rectification-v4/evidence-ledger";
import { rectificationV4Context, rectificationV4Error, requestBody, routeId } from "../../../../../_server";

export const runtime = "nodejs";

export async function POST(request: Request, { params }: { params: Promise<{ caseId: string; eventId: string }> }) {
  try {
    const body = await requestBody(request, reviseEventRequestSchema);
    const context = await rectificationV4Context();
    const values = await params;
    const caseId = routeId(values.caseId);
    const eventId = routeId(values.eventId);
    const current = await context.service.loadCase(context.userId, caseId);
    if (!current) return NextResponse.json({ error: "没有找到这次生时校正记录。" }, { status: 404 });
    const revision = appendEventRevision(current.events, {
      eventId,
      domain: body.domain,
      eventKind: body.eventKind,
      summary: body.summary,
      rawText: body.rawText,
      dateRange: body.dateRange,
      scoreability: body.scoreability,
    });
    return NextResponse.json(await context.service.reviseEvent({
      userId: context.userId,
      caseId,
      actionId: body.actionId,
      expectedCaseVersion: body.expectedCaseVersion,
      revision,
    }), { status: 202 });
  } catch (error) {
    return rectificationV4Error(error);
  }
}
