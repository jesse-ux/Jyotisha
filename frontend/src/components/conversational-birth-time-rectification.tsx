"use client";

import type { PublicLanguageModel } from "../lib/public-models.ts";
import type { ChatMessage } from "../lib/chat-message-view.ts";
import { AgenticRectificationChat } from "./rectification-agentic-chat.tsx";

export type ConversationalBirthTimeRectificationProps = Readonly<{
  sessionId: string;
  initialMessages: readonly ChatMessage[];
  models: readonly PublicLanguageModel[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  onMessagesChange?: (messages: ChatMessage[]) => void;
  onCompleted?: () => void;
  pendingConsultationQuestion?: string | null;
  onPendingChange?: (pending: boolean) => void;
  onProfileIncomplete?: () => void;
  onSaved?: (time: string) => void;
}>;

export function ConversationalBirthTimeRectification(props: ConversationalBirthTimeRectificationProps) {
  return <AgenticRectificationChat {...props} />;
}
