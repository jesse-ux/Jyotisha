import { z } from "zod";
import {
  RectificationHandoffServiceError,
  type RectificationV4HandoffService,
} from "../rectification-handoff-service.ts";

const identity = {
  caseId: z.string().uuid(),
  caseVersion: z.number().int().nonnegative(),
  actionId: z.string().uuid(),
  question: z.string().trim().min(1).max(500),
} as const;

const commandSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("attach"), ...identity }).strict(),
  z.object({ type: z.literal("claim"), ...identity }).strict(),
]);

export type RectificationV4HandoffRouteDependencies = Readonly<{
  authenticate(): Promise<Readonly<{ userId: string }> | null>;
  service(): RectificationV4HandoffService;
}>;

function failure(error: unknown) {
  if (error instanceof RectificationHandoffServiceError) {
    if (error.code === "not_found") {
      return Response.json({ code: "handoff_not_found", message: "没有找到可继续的原问题。" }, { status: 404 });
    }
    if (error.code === "stale") {
      return Response.json({ code: "stale_case", message: "校正结果已经更新，请刷新后重试。" }, { status: 409 });
    }
    if (error.code === "conflict") {
      return Response.json({ code: "handoff_conflict", message: "原问题状态已经变化，请刷新后查看。" }, { status: 409 });
    }
  }
  return Response.json({ code: "handoff_unavailable", message: "暂时无法保存或继续原问题，请稍后重试。" }, { status: 503 });
}

export function createRectificationV4HandoffHandlers(
  dependencies: RectificationV4HandoffRouteDependencies,
) {
  return Object.freeze({
    async get(request: Request) {
      const authenticated = await dependencies.authenticate();
      if (!authenticated) {
        return Response.json({ code: "authentication_required", message: "登录后才能继续原问题。" }, { status: 401 });
      }
      const caseId = new URL(request.url).searchParams.get("caseId") ?? undefined;
      if (caseId && !z.string().uuid().safeParse(caseId).success) {
        return Response.json({ code: "invalid_case", message: "生时校正记录格式不正确。" }, { status: 400 });
      }
      try {
        const handoff = await dependencies.service().load({ userId: authenticated.userId, caseId });
        return handoff ? Response.json(handoff) : new Response(null, { status: 204 });
      } catch (error) {
        return failure(error);
      }
    },

    async post(request: Request) {
      const authenticated = await dependencies.authenticate();
      if (!authenticated) {
        return Response.json({ code: "authentication_required", message: "登录后才能保存或继续原问题。" }, { status: 401 });
      }
      const parsed = commandSchema.safeParse(await request.json().catch(() => null));
      if (!parsed.success) {
        return Response.json({ code: "invalid_command", message: "原问题交接请求格式不正确。" }, { status: 400 });
      }
      try {
        const service = dependencies.service();
        const input = { userId: authenticated.userId, ...parsed.data };
        return Response.json(parsed.data.type === "attach"
          ? await service.attach(input)
          : await service.claim(input));
      } catch (error) {
        return failure(error);
      }
    },
  });
}
