import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";
import { chatSessionWriteSchema } from "@/lib/chat-session-write-contract";

type RouteContext = { params: Promise<{ id: string }> };

export async function PATCH(request: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const parsed = chatSessionWriteSchema.safeParse(await request.json().catch(() => null));
    if (!parsed.success) return NextResponse.json({ error: "聊天记录格式不正确" }, { status: 400 });
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) return NextResponse.json({ error: "请先登录" }, { status: 401 });
    const { data, error } = await supabase
      .from("chat_sessions")
      .update(parsed.data)
      .eq("id", id)
      .eq("user_id", user.id)
      .select("id")
      .maybeSingle();
    if (error) return NextResponse.json({ error: "聊天记录暂时无法同步" }, { status: 500 });
    if (!data) return NextResponse.json({ error: "聊天记录不存在或已被删除" }, { status: 404 });
    return NextResponse.json({ ok: true });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: "聊天记录暂时无法同步" }, { status: 500 });
  }
}

export async function DELETE(_request: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const supabase = await createServerSupabaseClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return NextResponse.json({ error: "请先登录" }, { status: 401 });

    const { count, error } = await supabase
      .from("chat_sessions")
      .delete({ count: "exact" })
      .eq("id", id)
      .eq("user_id", user.id);
    if (error) throw error;
    if (count !== 1) return NextResponse.json({ error: "聊天记录不存在或无权删除" }, { status: 404 });
    return NextResponse.json({ ok: true });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: error instanceof Error ? error.message : "删除聊天记录失败" }, { status: 500 });
  }
}
