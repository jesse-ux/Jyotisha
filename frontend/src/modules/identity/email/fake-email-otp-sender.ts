import type {
  EmailOtpMessage,
  EmailOtpSender,
} from "../contracts.ts";

export class FakeEmailOtpSender implements EmailOtpSender {
  readonly messages: EmailOtpMessage[] = [];

  async send(message: EmailOtpMessage): Promise<void> {
    this.messages.push({ ...message });
  }
}
