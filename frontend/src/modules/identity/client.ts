import { createAuthClient } from "better-auth/react";
import { emailOTPClient } from "better-auth/client/plugins";

interface AuthClientResult {
  data: unknown;
  error: unknown;
}

export interface SelfHostedAuthClient {
  emailOtp: {
    sendVerificationOtp(input: {
      email: string;
      type: "sign-in";
    }): Promise<AuthClientResult>;
    requestPasswordReset?(input: { email: string }): Promise<AuthClientResult>;
    resetPassword?(input: {
      email: string;
      otp: string;
      password: string;
    }): Promise<AuthClientResult>;
  };
  signIn: {
    emailOtp(input: {
      email: string;
      otp: string;
    }): Promise<AuthClientResult>;
    email?(input: {
      email: string;
      password: string;
    }): Promise<AuthClientResult>;
  };
  signOut?(): Promise<AuthClientResult>;
}

export interface SelfHostedAuthActions {
  send(email: string): Promise<void>;
  verify(email: string, otp: string): Promise<void>;
  signInWithPassword(email: string, password: string): Promise<void>;
  requestPasswordReset(email: string): Promise<void>;
  resetPassword(email: string, otp: string, password: string): Promise<void>;
  hasPassword(): Promise<boolean>;
  setPassword(password: string): Promise<void>;
  signOut(): Promise<void>;
}

type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function createSelfHostedAuthActions(
  client: SelfHostedAuthClient,
  fetcher: Fetcher = fetch,
): SelfHostedAuthActions {
  return {
    async send(email) {
      const result = await client.emailOtp.sendVerificationOtp({
        email: normalizeEmail(email),
        type: "sign-in",
      });
      if (result.error) {
        throw new Error("暂时无法发送验证码，请稍后再试");
      }
    },
    async verify(email, otp) {
      const result = await client.signIn.emailOtp({
        email: normalizeEmail(email),
        otp,
      });
      if (result.error) {
        throw new Error("验证码错误或已过期，请重新获取");
      }
    },
    async signInWithPassword(email, password) {
      if (!client.signIn.email) throw new Error("邮箱或密码错误");
      const result = await client.signIn.email({
        email: normalizeEmail(email),
        password,
      });
      if (result.error) throw new Error("邮箱或密码错误");
    },
    async requestPasswordReset(email) {
      if (!client.emailOtp.requestPasswordReset) {
        throw new Error("暂时无法发送验证码，请稍后再试");
      }
      const result = await client.emailOtp.requestPasswordReset({
        email: normalizeEmail(email),
      });
      if (result.error) {
        throw new Error("暂时无法发送验证码，请稍后再试");
      }
    },
    async resetPassword(email, otp, password) {
      if (!client.emailOtp.resetPassword) {
        throw new Error("验证码错误或已过期，请重新获取");
      }
      const result = await client.emailOtp.resetPassword({
        email: normalizeEmail(email),
        otp,
        password,
      });
      if (result.error) {
        throw new Error("验证码错误或已过期，请重新获取");
      }
    },
    async hasPassword() {
      const response = await fetcher("/api/account/password", {
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error("暂时无法确认密码状态，请稍后再试");
      const body = (await response.json()) as { hasPassword?: unknown };
      if (typeof body.hasPassword !== "boolean") {
        throw new Error("暂时无法确认密码状态，请稍后再试");
      }
      return body.hasPassword;
    },
    async setPassword(password) {
      const response = await fetcher("/api/account/password", {
        method: "POST",
        credentials: "same-origin",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ newPassword: password }),
      });
      if (response.status === 409) {
        throw new Error("此账户已设置密码，原密码未被更改");
      }
      if (!response.ok) throw new Error("暂时无法设置密码，请稍后再试");
    },
    async signOut() {
      if (!client.signOut) throw new Error("退出失败，请稍后再试");
      const result = await client.signOut();
      if (result.error) throw new Error("退出失败，请稍后再试");
    },
  };
}

export type SelfHostedOtpClient = SelfHostedAuthClient;
export type SelfHostedOtpActions = SelfHostedAuthActions;
export const createSelfHostedOtpActions = createSelfHostedAuthActions;

const authClient = createAuthClient({ plugins: [emailOTPClient()] });

export const selfHostedAuthActions = createSelfHostedAuthActions(
  authClient as unknown as SelfHostedAuthClient,
);

export const selfHostedOtpActions = selfHostedAuthActions;
