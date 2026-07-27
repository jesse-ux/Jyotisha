"use client";

import type { PublicLanguageModel } from "../lib/public-models.ts";
import {
  RectificationV4Panel,
  type RectificationV4Continuation,
} from "./rectification-v4-panel.tsx";

export type ConversationalBirthTimeRectificationProps = Readonly<{
  models: readonly PublicLanguageModel[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  pendingConsultationQuestion?: string | null;
  continuationPending?: boolean;
  onPendingChange?: (pending: boolean) => void;
  onContinueOriginalQuestion?: (continuation: RectificationV4Continuation) => void;
}>;

export function ConversationalBirthTimeRectification(props: ConversationalBirthTimeRectificationProps) {
  return <RectificationV4Panel {...props} />;
}
