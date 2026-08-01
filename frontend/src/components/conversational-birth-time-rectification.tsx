"use client";

import { useEffect, useState } from "react";
import { loadActiveRectificationV4, transitionRectificationV4 } from "../lib/rectification-v4/client.ts";
import type { RectificationV4ApiResponse } from "../lib/rectification-v4/contracts.ts";
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
 * Lets the user explicitly continue or end an existing v4 evidence case, and
 * otherwise opens the agentic chat where the LLM drives the full Jyotish
 * rectification methodology with the engine as its computation layer.
 */
export function ConversationalBirthTimeRectification(props: ConversationalBirthTimeRectificationProps) {
  const [mode, setMode] = useState<"loading" | "choice" | "v4" | "agentic">("loading");
  const [existing, setExisting] = useState<RectificationV4ApiResponse | null>(null);
  const [switching, setSwitching] = useState(false);
  const [switchError, setSwitchError] = useState("");

  useEffect(() => {
    let mounted = true;
    void (async () => {
      const existing = await loadActiveRectificationV4().catch(() => null);
      if (mounted) {
        setExisting(existing);
        setMode(existing ? "choice" : "agentic");
      }
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

  if (mode === "choice" && existing) {
    const startAgentic = async () => {
      setSwitching(true);
      setSwitchError("");
      try {
        await transitionRectificationV4(existing.case.id, existing.case.version, "abandon");
        setMode("agentic");
      } catch {
        setSwitchError("无法结束旧版校正，请稍后再试。");
      } finally {
        setSwitching(false);
      }
    };
    return (
      <>
        <section className="conversation" aria-label="生时校正版本选择" aria-busy={switching}>
          <div className="message-list" aria-live="polite">
            <ChatMessageRow
              message={{
                role: "assistant",
                text: "检测到一段尚未结束的旧版生时校正。你可以继续保留进度，或结束旧版并使用新版 Agent 重新开始。",
                renderKey: "rectification-version-choice",
                state: "settled",
              }}
            />
            {switchError && <p className="error-message" role="alert">{switchError}</p>}
          </div>
        </section>
        <div className="composer-wrap">
          <div className="composer-suggestions" aria-label="选择生时校正版本">
            <button type="button" disabled={switching} onClick={() => setMode("v4")}>继续旧版校正</button>
            <button type="button" disabled={switching} onClick={() => void startAgentic()}>
              {switching ? "正在结束旧版校正…" : "结束旧版并使用新版 Agent"}
            </button>
          </div>
        </div>
      </>
    );
  }

  if (mode === "v4") {
    return <RectificationV4Panel {...props} onUseAgentic={() => setMode("agentic")} />;
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
