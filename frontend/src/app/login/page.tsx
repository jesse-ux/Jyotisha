import { headers } from "next/headers";

import { EmailOtpLogin } from "@/components/email-otp-login";
import {
  isSelfHostedIdentityEnabled,
  readIdentityConfig,
  readSelfHostedIdentityConfig,
} from "@/modules/identity/config";
import { resolveIdentitySurface } from "@/modules/identity/host";

export const dynamic = "force-dynamic";

export default async function LoginPage() {
  const config = readIdentityConfig(process.env);
  let provider = config.provider;
  let passwordEnabled = false;
  let passwordOnly = false;
  if (isSelfHostedIdentityEnabled(process.env)) {
    const selfHosted = readSelfHostedIdentityConfig(process.env);
    const surface = resolveIdentitySurface(
      (await headers()).get("host"),
      selfHosted,
    );
    if (surface === "admin") provider = "self-hosted";
    passwordEnabled = provider === "self-hosted";
    passwordOnly = surface === "admin";
  }
  return (
    <EmailOtpLogin
      provider={provider}
      passwordEnabled={passwordEnabled}
      passwordOnly={passwordOnly}
    />
  );
}
