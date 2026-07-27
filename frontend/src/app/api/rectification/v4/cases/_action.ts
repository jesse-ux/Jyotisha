import { NextResponse } from "next/server";
import { caseActionRequestSchema } from "@/lib/rectification-v4/contracts";
import { rectificationV4Context, requestBody, routeId } from "../_server";

export async function transitionCase(
  request: Request,
  params: Promise<{ caseId: string }>,
  kind: "pause" | "resume" | "abandon",
) {
  const body = await requestBody(request, caseActionRequestSchema);
  const context = await rectificationV4Context();
  return NextResponse.json(await context.service.transition({
    ...body,
    userId: context.userId,
    caseId: routeId((await params).caseId),
    kind,
  }));
}
