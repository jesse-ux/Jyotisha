import type {
  EmailOtpMessage,
  EmailOtpSender,
  EmailOtpType,
} from "../contracts.ts";

const resendEndpoint = "https://api.resend.com/emails";
const safeDeliveryError = "OTP email delivery failed";

const subjectByType: Record<EmailOtpType, string> = {
  "sign-in": "Your Jyotisha sign-in code",
  "email-verification": "Verify your Jyotisha email",
  "forget-password": "Reset your Jyotisha password",
};

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return entities[character];
  });
}

export interface ResendEmailOtpSenderOptions {
  apiKey: string;
  from: string;
  fetchImpl?: typeof fetch;
}

export class ResendEmailOtpSender implements EmailOtpSender {
  private readonly apiKey: string;
  private readonly from: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: ResendEmailOtpSenderOptions) {
    this.apiKey = options.apiKey;
    this.from = options.from;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async send(message: EmailOtpMessage): Promise<void> {
    const escapedOtp = escapeHtml(message.otp);
    const subject = subjectByType[message.type];

    try {
      const response = await this.fetchImpl(resendEndpoint, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
          "Idempotency-Key": message.idempotencyKey,
          "User-Agent": "jyotisha-identity/1.0",
        },
        body: JSON.stringify({
          from: this.from,
          to: [message.email],
          subject,
          text: `${subject}: ${message.otp}. This code expires in five minutes.`,
          html: `<p>${escapeHtml(subject)}</p><p><strong>${escapedOtp}</strong></p><p>This code expires in five minutes.</p>`,
        }),
      });

      if (!response.ok) throw new Error(safeDeliveryError);
    } catch {
      throw new Error(safeDeliveryError);
    }
  }
}
