import { EmailOtpLogin } from "@/components/email-otp-login";
import { readIdentityConfig } from "@/modules/identity/config";

export default function LoginPage() {
  const config = readIdentityConfig(process.env);
  return <EmailOtpLogin provider={config.provider} />;
}
