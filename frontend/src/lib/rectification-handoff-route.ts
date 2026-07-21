import { z } from "zod";
import {
  RectificationHandoffServiceError,
  type RectificationHandoffService,
} from "./rectification-handoff-service.ts";

const identity = {
  caseId: z.string().uuid(),
  turnVersion: z.number().int().nonnegative(),
  actionId: z.string().uuid(),
  question: z.string().trim().min(1).max(500),
} as const;

const commandSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("attach"), ...identity }).strict(),
  z.object({ type: z.literal("claim"), ...identity }).strict(),
]);

type Authenticated = Readonly<{ userId: string }>;

export type RectificationHandoffRouteDependencies = Readonly<{
  authenticate(): Promise<Authenticated | null>;
  service(): RectificationHandoffService;
}>;

function publicFailure(error: unknown) {
  if (error instanceof RectificationHandoffServiceError) {
    if (error.code === "not_found") {
      return Response.json(
        { code: "handoff_not_found", message: "没有找到可继续的原问题。" },
        { status: 404 },
      );
    }
    if (error.code === "stale") {
      return Response.json(
        { code: "stale_turn", message: "校正状态已经更新，请刷新后重试。" },
        { status: 409 },
      );
    }
    if (error.code === "conflict") {
      return Response.json(
        { code: "handoff_conflict", message: "原问题状态已经变化，请刷新后查看。" },
        { status: 409 },
      );
    }
  }
  return Response.json(
    { code: "handoff_unavailable", message: "暂时无法保存或继续原问题，请稍后重试。" },
    { status: 503 },
  );
}

export function createRectificationHandoffHandlers(
  dependencies: RectificationHandoffRouteDependencies,
) {
  return Object.freeze({
    async get() {
      const authenticated = await dependencies.authenticate();
      if (!authenticated) {
        return Response.json(
          { code: "authentication_required", message: "登录后才能继续原问题。" },
          { status: 401 },
        );
      }
      try {
        const handoff = await dependencies.service().load({ userId: authenticated.userId });
        return handoff
          ? Response.json(handoff)
          : new Response(null, { status: 204 });
      } catch (error) {
        return publicFailure(error);
      }
    },

    async post(request: Request) {
      const authenticated = await dependencies.authenticate();
      if (!authenticated) {
        return Response.json(
          { code: "authentication_required", message: "登录后才能保存或继续原问题。" },
          { status: 401 },
        );
      }
      const parsed = commandSchema.safeParse(await request.json().catch(() => null));
      if (!parsed.success) {
        return Response.json(
          { code: "invalid_command", message: "原问题交接请求格式不正确。" },
          { status: 400 },
        );
      }
      try {
        const service = dependencies.service();
        const input = { userId: authenticated.userId, ...parsed.data };
        const result = parsed.data.type === "attach"
          ? await service.attach(input)
          : await service.claim(input);
        return Response.json(result);
      } catch (error) {
        return publicFailure(error);
      }
    },
  });
}
