import { NextResponse } from "next/server";
import { rectificationV4Context, rectificationV4Error } from "../../_server";

export const runtime = "nodejs";

export async function GET() {
  try {
    const context = await rectificationV4Context();
    const result = await context.service.loadActive(context.userId);
    return result ? NextResponse.json(result) : new NextResponse(null, { status: 204 });
  } catch (error) {
    return rectificationV4Error(error);
  }
}
