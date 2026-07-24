import { NextResponse } from "next/server";
import { birthLocationSearchQuerySchema } from "@/lib/location-contract";
import { searchGlobalBirthLocations } from "@/lib/geoapify-location-service";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const supabase = await createServerSupabaseClient();
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return NextResponse.json({ error: "请先登录" }, { status: 401 });

  const url = new URL(request.url);
  const parsed = birthLocationSearchQuerySchema.safeParse(Object.fromEntries(url.searchParams));
  if (!parsed.success) return NextResponse.json({
    error: "地点搜索参数不正确",
    details: parsed.error.flatten(),
  }, { status: 400 });

  const result = await searchGlobalBirthLocations(parsed.data);
  const status = result.status === "ok" ? 200 : 503;
  return NextResponse.json(result, { status });
}
