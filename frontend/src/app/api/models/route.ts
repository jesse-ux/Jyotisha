import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { publicLanguageModelCatalog } from "@/mastra/model";

export const runtime = "nodejs";

export async function GET() {
  let supabase: Awaited<ReturnType<typeof createServerSupabaseClient>>;
  try {
    supabase = await createServerSupabaseClient();
  } catch (error) {
    if (error instanceof Error) {
      return NextResponse.json(
        { error: "服务尚未配置", message: "请先配置 Supabase 环境变量。" },
        { status: 503 },
      );
    }
    throw error;
  }

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: "请先登录", message: "登录后才能读取可用模型。" },
      { status: 401 },
    );
  }

  const catalog = publicLanguageModelCatalog();
  if (!catalog.defaultModelId || catalog.models.length === 0) {
    return NextResponse.json(
      { error: "模型服务尚未配置", message: "当前没有可用的咨询模型。" },
      { status: 503 },
    );
  }

  return NextResponse.json(catalog);
}
