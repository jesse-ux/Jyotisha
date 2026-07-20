const unsafeImplementationMessage = /expected pattern|failed to fetch|networkerror|load failed|domexception|syntaxerror/i;

export function birthTimeUserError(error: unknown): string {
  const message = error instanceof Error ? error.message.trim() : "";
  if (!message || unsafeImplementationMessage.test(message) || !/[\u3400-\u9fff]/u.test(message)) {
    return "候选时间暂时无法保存，请检查网络后重试。";
  }
  return message;
}
