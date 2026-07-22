export type IdentitySurface = "user" | "admin";

export type EmailOtpType =
  | "sign-in"
  | "email-verification"
  | "forget-password"
  | "change-email";

export interface EmailOtpMessage {
  email: string;
  otp: string;
  type: EmailOtpType;
  idempotencyKey: string;
}

export interface EmailOtpSender {
  send(message: EmailOtpMessage): Promise<void>;
}

export interface IdentityUser {
  id: string;
  email: string;
  emailVerified: boolean;
  name: string;
  image: string | null;
  role: string[];
}

export interface IdentitySession {
  user: IdentityUser;
  expiresAt: Date;
}
