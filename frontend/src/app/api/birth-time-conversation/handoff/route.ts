import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { createRectificationHandoffService } from "@/lib/rectification-handoff-service";
import {
  createRectificationHandoffHandlers,
  type RectificationHandoffRouteDependencies,
} from "@/lib/rectification-handoff-route";

export const runtime = "nodejs";

const productionDependencies: RectificationHandoffRouteDependencies = {
  async authenticate() {
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error } = await supabase.auth.getUser();
    return error || !user ? null : { userId: user.id };
  },
  service() {
    return createRectificationHandoffService(createAdminSupabaseClient());
  },
};

const handlers = createRectificationHandoffHandlers(productionDependencies);

export async function GET() {
  try {
    return await handlers.get();
  } catch {
    return Response.json(
      { code: "handoff_unavailable", message: "原问题交接服务暂时不可用。" },
      { status: 503 },
    );
  }
}

export async function POST(request: Request) {
  try {
    return await handlers.post(request);
  } catch {
    return Response.json(
      { code: "handoff_unavailable", message: "原问题交接服务暂时不可用。" },
      { status: 503 },
    );
  }
}
