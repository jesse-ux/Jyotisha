import { NextResponse } from "next/server";
import { createCaseRequestSchema } from "@/lib/rectification-v4/contracts";
import { calculationSpecForUser, rectificationV4Context, rectificationV4Error, requestBody } from "../_server";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const body = await requestBody(request, createCaseRequestSchema);
    const context = await rectificationV4Context();
    return NextResponse.json(await context.service.createCase({
      userId: context.userId,
      actionId: body.actionId,
      calculationSpec: await calculationSpecForUser(context.auth, context.userId),
    }));
  } catch (error) {
    return rectificationV4Error(error);
  }
}
