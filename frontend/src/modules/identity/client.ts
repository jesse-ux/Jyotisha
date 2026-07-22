import { createAuthClient } from "better-auth/react";
import { emailOTPClient } from "better-auth/client/plugins";

interface OtpClientResult {
  data: unknown;
  error: unknown;
}

export interface SelfHostedOtpClient {
  emailOtp: {
    sendVerificationOtp(input: {
      email: string;
      type: "sign-in";
    }): Promise<OtpClientResult>;
  };
  signIn: {
    emailOtp(input: {
      email: string;
      otp: string;
    }): Promise<OtpClientResult>;
  };
  signOut?(): Promise<OtpClientResult>;
}

export interface SelfHostedOtpActions {
  send(email: string): Promise<void>;
  verify(email: string, otp: string): Promise<void>;
  signOut(): Promise<void>;
}

export function createSelfHostedOtpActions(
  client: SelfHostedOtpClient,
): SelfHostedOtpActions {
  return {
    async send(email) {
      const result = await client.emailOtp.sendVerificationOtp({
        email: email.trim().toLowerCase(),
        type: "sign-in",
      });
      if (result.error) {
        throw new Error("暂时无法发送验证码，请稍后再试");
      }
    },
    async verify(email, otp) {
      const result = await client.signIn.emailOtp({
        email: email.trim().toLowerCase(),
        otp,
      });
      if (result.error) {
        throw new Error("验证码错误或已过期，请重新获取");
      }
    },
    async signOut() {
      if (!client.signOut) throw new Error("退出失败，请稍后再试");
      const result = await client.signOut();
      if (result.error) throw new Error("退出失败，请稍后再试");
    },
  };
}

const authClient = createAuthClient({ plugins: [emailOTPClient()] });

export const selfHostedOtpActions = createSelfHostedOtpActions(
  authClient as SelfHostedOtpClient,
);
