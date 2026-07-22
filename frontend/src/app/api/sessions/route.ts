import { NextResponse } from "next/server";
import { chatSessionCreateSchema } from "@/lib/chat-session-write-contract";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export async function GET() {
  try {
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) return NextResponse.json({ error: "请先登录" }, { status: 401 });
    const { data, error } = await supabase
      .from("chat_sessions")
      .select("id,title,theme,model_id,messages,session_type,rectification_case_id,updated_at")
      .eq("user_id", user.id)
      .order("updated_at", { ascending: false });
    if (error) return NextResponse.json({ error: "聊天记录暂时无法读取" }, { status: 500 });
    return NextResponse.json({ sessions: data ?? [] });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "数据库尚未配置", code: "DATABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: "聊天记录暂时无法读取" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) return NextResponse.json({ error: "请先登录" }, { status: 401 });
    const parsed = chatSessionCreateSchema.safeParse(await request.json().catch(() => null));
    if (!parsed.success) return NextResponse.json({ error: "聊天记录格式不正确" }, { status: 400 });
    const { id, ...values } = parsed.data;
    const { error } = await supabase.from("chat_sessions").insert({
      id,
      user_id: user.id,
      ...values,
    });
    if (error) return NextResponse.json({ error: "聊天记录暂时无法同步" }, { status: 500 });
    return NextResponse.json({ ok: true }, { status: 201 });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: "聊天记录暂时无法同步" }, { status: 500 });
  }
}
