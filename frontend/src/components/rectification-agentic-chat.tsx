"use client";

import { ArrowUp } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { parseAgentReply } from "@/lib/agent-reply";
import type { ChatMessageView } from "@/lib/chat-message-view";
import type { PublicLanguageModel } from "@/lib/public-models";
import { ChatMessageRow } from "./chat-message-row";
import { ModelSelector } from "./model-selector";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";

type AgenticRectificationChatProps = Readonly<{
  models: readonly PublicLanguageModel[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  pendingConsultationQuestion?: string | null;
  onPendingChange?: (pending: boolean) => void;
  onProfileIncomplete?: () => void;
  onSaved?: (time: string) => void;
}>;

type RenderMessage = ChatMessageView;

const savedSentinel = /<!--AYANAM_RECTIFICATION_SAVED:(\d{2}:\d{2})-->/;

type AgenticRectificationRequest = Readonly<
  | { action: "opening" }
  | { action: "message"; message: string }
>;

export function AgenticRectificationChat(props: AgenticRectificationChatProps) {
  const {
    models,
    selectedModelId,
    onSelectModel,
    pendingConsultationQuestion,
    onPendingChange,
    onProfileIncomplete,
    onSaved,
  } = props;
  const pendingQuestion = pendingConsultationQuestion?.trim();
  const [messages, setMessages] = useState<RenderMessage[]>(() => pendingQuestion ? [{
    role: "assistant",
    text: `我先陪你把出生时间范围核对清楚，之后再回到你原来的问题：“${pendingQuestion}”`,
    renderKey: "agentic-pending-consultation",
    state: "settled",
  }] : []);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [savedTime, setSavedTime] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const composer = useRef<HTMLTextAreaElement>(null);
  const conversationEnd = useRef<HTMLDivElement>(null);
  const keyCounter = useRef(0);
  const openingStarted = useRef(false);

  const setPending = useCallback((value: boolean) => {
    setBusy(value);
    onPendingChange?.(value);
  }, [onPendingChange]);

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    conversationEnd.current?.scrollIntoView({
      behavior: busy || reduceMotion ? "auto" : "smooth",
      block: "end",
    });
  }, [busy, error, messages.length, savedTime]);

  const send = useCallback(async (request: AgenticRectificationRequest, showUserMessage = true) => {
    const trimmed = request.action === "message" ? request.message.trim() : "";
    if ((request.action === "message" && !trimmed) || busy) return;
    setError("");
    setSavedTime(null);
    setSuggestions([]);
    setPending(true);

    keyCounter.current += 1;
    const requestId = globalThis.crypto.randomUUID();
    const history = messages
      .filter((message) => message.state === "settled")
      .map((message) => ({ role: message.role, text: message.text }));
    const turnKey = keyCounter.current;
    const userRenderKey = `agentic-user-${turnKey}`;
    const assistantRenderKey = `agentic-assistant-${turnKey}`;

    setMessages((current) => [
      ...current,
      ...(showUserMessage && request.action === "message"
        ? [{ role: "user", text: trimmed, renderKey: userRenderKey, state: "settled" } satisfies RenderMessage]
        : []),
      { role: "assistant", text: "", renderKey: assistantRenderKey, state: "thinking" },
    ]);
    setDraft("");

    let raw = "";
    try {
      const response = await fetch("/api/rectification/agent", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          requestId,
          modelId: selectedModelId,
          history,
          action: request.action,
          ...(request.action === "message" ? { message: trimmed } : {}),
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        const message = payload?.message || payload?.error || `请求失败（${response.status}）`;
        if (payload?.code === "profile_incomplete") {
          onProfileIncomplete?.();
          return;
        }
        if (response.status === 402) setError(`咨询点数不足：${message}`);
        else if (response.status === 401) setError("请先登录。");
        else setError(message);
        return;
      }
      if (!response.body) {
        setError("服务暂时不可用，请稍后再试。");
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.trim()) continue;
          let event: { type: string; text?: string; message?: string };
          try {
            event = JSON.parse(line) as { type: string; text?: string; message?: string };
          } catch {
            continue;
          }
          if (event.type === "delta" && typeof event.text === "string") {
            raw += event.text;
            const parsed = parseAgentReply(raw, "general");
            setMessages((current) => current.map((message) => message.renderKey === assistantRenderKey
              ? { ...message, text: parsed.text, state: "streaming" }
              : message));
            setSuggestions(parsed.suggestions);
            const saved = raw.match(savedSentinel);
            if (saved) setSavedTime(saved[1]);
          } else if (event.type === "error") {
            setError(event.message || "生时校正暂时不可用，请稍后再试。");
          }
        }
      }

      const parsed = parseAgentReply(raw, "general");
      setMessages((current) => current.map((message) => message.renderKey === assistantRenderKey
        ? { ...message, text: parsed.text, state: "settled" }
        : message));
      setSuggestions(parsed.suggestions);
      const saved = raw.match(savedSentinel);
      if (saved) {
        setSavedTime(saved[1]);
        onSaved?.(saved[1]);
      }
    } catch {
      setError("生时校正暂时不可用，请稍后再试。");
      setMessages((current) => current.filter((message) => message.renderKey !== assistantRenderKey));
    } finally {
      setPending(false);
    }
  }, [busy, messages, onProfileIncomplete, onSaved, selectedModelId, setPending]);

  useEffect(() => {
    if (openingStarted.current) return;
    openingStarted.current = true;
    void send({ action: "opening" }, false);
  }, [send]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    await send({ action: "message", message: draft });
  }

  const canSend = !busy;

  return (
    <>
      <section className="conversation" aria-label="生时校正对话" aria-busy={busy}>
        <div className="message-list" aria-live="polite">
          {messages.map((message) => <ChatMessageRow key={message.renderKey} message={message} />)}
          {savedTime && (
            <p className="error-message" role="status">
              出生时间已更新为 {savedTime}，后续排盘将使用该时间。
            </p>
          )}
          {error && <p className="error-message" role="alert">{error}</p>}
          <div ref={conversationEnd} />
        </div>
      </section>

      <div className="composer-wrap">
        {suggestions.length > 0 && !busy && (
          <div className="composer-suggestions" aria-label="推荐继续提问">
            {suggestions.map((question) => (
              <button key={question} type="button" onClick={() => void send({ action: "message", message: question })}>{question}</button>
            ))}
          </div>
        )}

        <form className="composer" onSubmit={submit}>
          <Textarea
            ref={composer}
            aria-label="继续描述你的经历或回答"
            value={draft}
            disabled={!canSend}
            placeholder="继续说你记得的人生经历，或回答刚才的问题…"
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
          />
          <Button aria-label="发送" disabled={!draft.trim() || !canSend} size="icon" type="submit">
            <ArrowUp aria-hidden="true" />
          </Button>
        </form>

        <div className="composer-footer">
          <ModelSelector
            models={models}
            selectedModelId={selectedModelId}
            disabled={busy}
            onSelect={onSelectModel}
          />
        </div>
      </div>
    </>
  );
}
