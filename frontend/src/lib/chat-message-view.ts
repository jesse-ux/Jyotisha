export type ChatMessage = {
  readonly role: "user" | "assistant";
  readonly text: string;
  readonly suggestions?: readonly string[];
};

export type ChatMessageView = ChatMessage & {
  readonly renderKey: string;
  readonly state: "settled" | "streaming" | "thinking";
};

export function chatMessageViews(
  messages: readonly ChatMessage[],
  loading: boolean,
  streamingText: string,
): readonly ChatMessageView[] {
  const settled = messages.map((message, index) => ({
    ...message,
    renderKey: `message-${index}`,
    state: "settled" as const,
  }));
  if (!loading || messages.at(-1)?.role === "assistant") return settled;

  return [
    ...settled,
    {
      role: "assistant",
      text: streamingText,
      renderKey: `message-${messages.length}`,
      state: streamingText ? "streaming" : "thinking",
    },
  ];
}
