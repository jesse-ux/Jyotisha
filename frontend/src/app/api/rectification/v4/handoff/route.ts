import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { createRectificationV4HandoffService } from "@/lib/rectification-handoff-service";
import {
  createRectificationV4HandoffHandlers,
  type RectificationV4HandoffRouteDependencies,
} from "@/lib/rectification-v4/handoff-route";

export const runtime = "nodejs";

const dependencies: RectificationV4HandoffRouteDependencies = {
  async authenticate() {
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error } = await supabase.auth.getUser();
    return error || !user ? null : { userId: user.id };
  },
  service() {
    return createRectificationV4HandoffService(createAdminSupabaseClient());
  },
};

const handlers = createRectificationV4HandoffHandlers(dependencies);

export async function GET(request: Request) {
  return handlers.get(request);
}

export async function POST(request: Request) {
  return handlers.post(request);
}
