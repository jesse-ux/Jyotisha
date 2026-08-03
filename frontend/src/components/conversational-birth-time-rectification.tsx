"use client";

import type { PublicLanguageModel } from "../lib/public-models.ts";
import { AgenticRectificationChat } from "./rectification-agentic-chat.tsx";

export type ConversationalBirthTimeRectificationProps = Readonly<{
  models: readonly PublicLanguageModel[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  pendingConsultationQuestion?: string | null;
  onPendingChange?: (pending: boolean) => void;
  onProfileIncomplete?: () => void;
  onSaved?: (time: string) => void;
}>;

export function ConversationalBirthTimeRectification(props: ConversationalBirthTimeRectificationProps) {
  return <AgenticRectificationChat {...props} />;
}
