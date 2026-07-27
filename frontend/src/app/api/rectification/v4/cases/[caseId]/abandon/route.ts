import { rectificationV4Error } from "../../../_server";
import { transitionCase } from "../../_action";

export const runtime = "nodejs";

export async function POST(request: Request, { params }: { params: Promise<{ caseId: string }> }) {
  try {
    return await transitionCase(request, params, "abandon");
  } catch (error) {
    return rectificationV4Error(error);
  }
}
