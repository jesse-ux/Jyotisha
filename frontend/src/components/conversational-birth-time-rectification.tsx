"use client";

import { useEffect, useState } from "react";
import { loadActiveRectificationV4 } from "../lib/rectification-v4/client.ts";
import type { PublicLanguageModel } from "../lib/public-models.ts";
import { AgenticRectificationChat } from "./rectification-agentic-chat.tsx";
import { ChatMessageRow } from "./chat-message-row.tsx";
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
  onSaved?: (time: string) => void;
}>;

/**
 * Birth-time rectification surface.
 *
 * Resumes an existing v4 evidence case when one is still in progress (so users
 * never lose a saved candidate range), and otherwise opens the agentic chat
 * where the LLM drives the full Jyotish rectification methodology with the
 * engine as its computation layer.
 */
export function ConversationalBirthTimeRectification(props: ConversationalBirthTimeRectificationProps) {
  const [mode, setMode] = useState<"loading" | "v4" | "agentic">("loading");

  useEffect(() => {
    let mounted = true;
    void (async () => {
      const existing = await loadActiveRectificationV4().catch(() => null);
      if (mounted) setMode(existing ? "v4" : "agentic");
    })();
    return () => { mounted = false; };
  }, []);

  if (mode === "loading") {
    return (
      <section className="conversation" aria-label="生时校正对话" aria-busy>
        <div className="message-list" aria-live="polite">
          <ChatLoadingRow />
          <div />
        </div>
      </section>
    );
  }

  if (mode === "v4") {
    return <RectificationV4Panel {...props} />;
  }

  return <AgenticRectificationChat {...props} />;
}

function ChatLoadingRow() {
  return (
    <ChatMessageRow
      message={{
        role: "assistant",
        text: "",
        renderKey: "agentic-loading",
        state: "thinking",
      }}
    />
  );
}
