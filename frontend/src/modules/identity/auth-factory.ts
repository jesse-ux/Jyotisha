import { createHmac } from "node:crypto";
import type { Pool } from "pg";
import type { BetterAuthOptions } from "better-auth";
import { admin, emailOTP, type EmailOTPOptions } from "better-auth/plugins";

import type { SelfHostedIdentityConfig } from "./config.ts";
import type { EmailOtpSender, IdentitySurface } from "./contracts.ts";
import { identityModelMapping } from "./model.ts";

export type AdminUserAuthorizer = (userId: string) => Promise<boolean>;

interface BuildAuthOptionsInput {
  surface: IdentitySurface;
  config: SelfHostedIdentityConfig;
  database: Pool;
  emailSender: EmailOtpSender;
  authorizeAdminUser?: AdminUserAuthorizer;
}

function otpIdempotencyKey(
  secret: string,
  email: string,
  otp: string,
  type: string,
): string {
  const digest = createHmac("sha256", secret)
    .update(type)
    .update("\0")
    .update(email.trim().toLowerCase())
    .update("\0")
    .update(otp)
    .digest("hex");
  return `otp-${digest}`;
}

export function createEmailOtpOptions(
  sender: EmailOtpSender,
  secret: string,
  disableSignUp: boolean,
): EmailOTPOptions {
  return {
    otpLength: 6,
    expiresIn: 300,
    allowedAttempts: 3,
    resendStrategy: "rotate",
    storeOTP: "hashed",
    disableSignUp,
    rateLimit: { window: 60, max: 3 },
    async sendVerificationOTP({ email, otp, type }) {
      await sender.send({
        email,
        otp,
        type,
        idempotencyKey: otpIdempotencyKey(secret, email, otp, type),
      });
    },
  };
}

export function buildAuthOptions({
  surface,
  config,
  database,
  emailSender,
  authorizeAdminUser,
}: BuildAuthOptionsInput): BetterAuthOptions {
  if (surface === "admin" && !authorizeAdminUser) {
    throw new Error("admin user authorizer is required");
  }

  const origin = surface === "user" ? config.userOrigin : config.adminOrigin;
  const secret = surface === "user" ? config.userSecret : config.adminSecret;

  return {
    appName: "Jyotisha",
    baseURL: origin,
    basePath: "/api/auth",
    secret,
    database,
    trustedOrigins: [origin],
    telemetry: { enabled: false },
    user: identityModelMapping.user,
    session: identityModelMapping.session,
    account: identityModelMapping.account,
    verification: identityModelMapping.verification,
    rateLimit: {
      storage: "database",
      window: 60,
      max: 30,
      ...identityModelMapping.rateLimit,
    },
    advanced: {
      database: { generateId: "uuid" },
      cookiePrefix:
        surface === "user" ? "jyotisha-user" : "jyotisha-admin",
      defaultCookieAttributes: {
        secure: true,
        httpOnly: true,
        sameSite: "lax",
        path: "/",
      },
    },
    plugins: [
      emailOTP(createEmailOtpOptions(emailSender, secret, surface === "admin")),
      admin({
        defaultRole: "user",
        adminRoles: ["admin"],
        schema: identityModelMapping.admin,
      }),
    ],
    ...(surface === "admin"
      ? {
          databaseHooks: {
            session: {
              create: {
                async before(session: { userId: string }) {
                  if (!(await authorizeAdminUser!(session.userId))) return false;
                },
              },
            },
          },
        }
      : {}),
  };
}
