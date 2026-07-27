import { getIdentityAuthServices } from "@/modules/identity/auth";
import {
  isSelfHostedIdentityEnabled,
  readSelfHostedIdentityConfig,
} from "@/modules/identity/config";
import { resolveIdentitySurface } from "@/modules/identity/host";

export const dynamic = "force-dynamic";

async function userSession(request: Request) {
  if (!isSelfHostedIdentityEnabled(process.env)) return null;
  const config = readSelfHostedIdentityConfig(process.env);
  if (resolveIdentitySurface(request.headers.get("host"), config) !== "user") {
    return null;
  }
  const services = getIdentityAuthServices();
  const session = await services.user.api.getSession({ headers: request.headers });
  return session ? { services, session } : null;
}

async function hasCredentialPassword(
  services: ReturnType<typeof getIdentityAuthServices>,
  userId: string,
): Promise<boolean> {
  const result = await services.pool.query(
    `
      select 1
      from identity.accounts
      where user_id = $1
        and provider_id = 'credential'
        and password is not null
      limit 1
    `,
    [userId],
  );
  return result.rowCount === 1;
}

export async function GET(request: Request): Promise<Response> {
  const context = await userSession(request);
  if (!context) {
    return Response.json({ error: "请先登录" }, { status: 401 });
  }
  return Response.json({
    hasPassword: await hasCredentialPassword(
      context.services,
      context.session.user.id,
    ),
  });
}

export async function POST(request: Request): Promise<Response> {
  const context = await userSession(request);
  if (!context) {
    return Response.json({ error: "请先登录" }, { status: 401 });
  }

  let body: { newPassword?: unknown };
  try {
    body = (await request.json()) as { newPassword?: unknown };
  } catch {
    return Response.json({ error: "请求格式错误" }, { status: 400 });
  }
  if (
    typeof body.newPassword !== "string" ||
    body.newPassword.length < 8 ||
    body.newPassword.length > 128
  ) {
    return Response.json({ error: "密码长度须为 8–128 位" }, { status: 400 });
  }
  if (
    await hasCredentialPassword(context.services, context.session.user.id)
  ) {
    return Response.json(
      { error: "此账户已设置密码，原密码未被更改" },
      { status: 409 },
    );
  }

  try {
    await context.services.user.api.setPassword({
      headers: request.headers,
      body: { newPassword: body.newPassword },
    });
    return Response.json({ ok: true });
  } catch {
    if (
      await hasCredentialPassword(context.services, context.session.user.id)
    ) {
      return Response.json(
        { error: "此账户已设置密码，原密码未被更改" },
        { status: 409 },
      );
    }
    return Response.json({ error: "暂时无法设置密码" }, { status: 500 });
  }
}
