import { NextResponse } from "next/server";

import { requireAdminSession } from "@/lib/admin/auth";
import { adminErrorResponse } from "@/lib/admin/http";

export const runtime = "nodejs";

export async function GET() {
  try {
    const { user, role } = await requireAdminSession();
    return NextResponse.json({
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role,
      },
    });
  } catch (error) {
    return adminErrorResponse(error);
  }
}
