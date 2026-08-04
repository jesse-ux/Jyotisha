"use client";

import { ArrowUp } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { parseAgentReply } from "@/lib/agent-reply";
import type { ChatMessage, ChatMessageView } from "@/lib/chat-message-view";
import type { PublicLanguageModel } from "@/lib/public-models";
import { ChatMessageRow } from "./chat-message-row";
import { ModelSelector } from "./model-selector";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";

type AgenticRectificationChatProps = Readonly<{
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
  onSaved?: (time: string, status: "accepted" | "confirmed") => void;
}>;

type RenderMessage = ChatMessageView;

type CandidateResult = Readonly<{
  resultId: string;
  candidates: readonly Readonly<{ rank: number; time: string; relative_support: number; tied_minute_count: number }>[];
  overallConfidence: "low" | "medium" | "high";
  marginPercent: number | null;
  selectionAllowed: boolean;
  confirmationAllowed: boolean;
  representativeTime: string | null;
  selectedTime: string | null;
  selectionStatus: "accepted" | "confirmed" | null;
}>;

const savedSentinel = /<!--AYANAM_RECTIFICATION_SAVED:(\d{2}:\d{2})-->/;

type AgenticRectificationRequest = Readonly<
  | { action: "opening" }
  | { action: "message"; message: string }
>;

export function AgenticRectificationChat(props: AgenticRectificationChatProps) {
  const {
    sessionId,
    initialMessages,
    models,
    selectedModelId,
    onSelectModel,
    onMessagesChange,
    onCompleted,
    pendingConsultationQuestion,
    onPendingChange,
    onProfileIncomplete,
    onSaved,
  } = props;
  const pendingQuestion = pendingConsultationQuestion?.trim();
  const [messages, setMessages] = useState<RenderMessage[]>(() => [
    ...initialMessages.map((message, index) => ({
      ...message,
      renderKey: `agentic-message-${index}`,
      state: "settled" as const,
    })),
    ...(initialMessages.length === 0 && pendingQuestion ? [{
      role: "assistant" as const,
      text: `我先陪你把出生时间范围核对清楚，之后再回到你原来的问题：“${pendingQuestion}”`,
      renderKey: "agentic-pending-consultation",
      state: "settled" as const,
    }] : []),
  ]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [savedTime, setSavedTime] = useState<string | null>(null);
  const [savedStatus, setSavedStatus] = useState<"accepted" | "confirmed" | null>(null);
  const [candidateResult, setCandidateResult] = useState<CandidateResult | null>(null);
  const [acceptingTime, setAcceptingTime] = useState<string | null>(null);
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
    setSuggestions([]);
    setPending(true);

    keyCounter.current += 1;
    const requestId = globalThis.crypto.randomUUID();
    const settledMessages = messages
      .filter((message) => message.state === "settled")
      .map((message) => ({
        role: message.role,
        text: message.text,
        ...(message.suggestions ? { suggestions: message.suggestions } : {}),
      }));
    const history = settledMessages.map((message) => ({ role: message.role, text: message.text }));
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
    let streamedSavedStatus: "accepted" | "confirmed" | null = null;
    try {
      const response = await fetch("/api/rectification/agent", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          requestId,
          sessionId,
          modelId: selectedModelId,
          history,
          action: request.action,
          ...(request.action === "message" ? { message: trimmed } : {}),
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        const message = payload?.message || payload?.error || `请求失败（${response.status}）`;
        setMessages((current) => current.filter((item) => item.renderKey !== assistantRenderKey));
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
        setMessages((current) => current.filter((message) => message.renderKey !== assistantRenderKey));
        setError("服务暂时不可用，请稍后再试。");
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let completed = false;
      let streamFailed = false;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.trim()) continue;
          let event: { type: string; text?: string; message?: string; result?: CandidateResult };
          try {
            event = JSON.parse(line) as { type: string; text?: string; message?: string; result?: CandidateResult };
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
          } else if (event.type === "candidates" && event.result) {
            setCandidateResult(event.result);
            if (event.result.selectedTime && event.result.selectionStatus) {
              setSavedTime(event.result.selectedTime);
              streamedSavedStatus = event.result.selectionStatus;
              setSavedStatus(event.result.selectionStatus);
            }
          } else if (event.type === "error") {
            streamFailed = true;
            setError(event.message || "生时校正暂时不可用，请稍后再试。");
          } else if (event.type === "done") {
            completed = true;
          }
        }
      }

      const parsed = parseAgentReply(raw, "general");
      const succeeded = completed && !streamFailed && Boolean(parsed.text);
      setMessages((current) => succeeded
        ? current.map((message) => message.renderKey === assistantRenderKey
          ? { ...message, text: parsed.text, suggestions: parsed.suggestions, state: "settled" }
          : message)
        : current.filter((message) => message.renderKey !== assistantRenderKey));
      setSuggestions(succeeded ? parsed.suggestions : []);
      if (succeeded) {
        onMessagesChange?.([
          ...settledMessages,
          ...(request.action === "message" ? [{ role: "user" as const, text: trimmed }] : []),
          { role: "assistant", text: parsed.text, suggestions: parsed.suggestions },
        ]);
        onCompleted?.();
      }
      const saved = raw.match(savedSentinel);
      if (saved) {
        setSavedTime(saved[1]);
        onSaved?.(saved[1], streamedSavedStatus ?? savedStatus ?? "accepted");
      }
    } catch {
      setError("生时校正暂时不可用，请稍后再试。");
      setMessages((current) => current.filter((message) => message.renderKey !== assistantRenderKey));
    } finally {
      setPending(false);
    }
  }, [busy, messages, onCompleted, onMessagesChange, onProfileIncomplete, onSaved, savedStatus, selectedModelId, sessionId, setPending]);

  useEffect(() => {
    let active = true;
    void fetch(`/api/rectification/agent?sessionId=${encodeURIComponent(sessionId)}`)
      .then((response) => response.ok ? response.json() : null)
      .then((payload) => {
        const result = payload?.result as CandidateResult | null | undefined;
        if (!active || !result) return;
        setCandidateResult(result);
        if (result.selectedTime && result.selectionStatus) {
          setSavedTime(result.selectedTime);
          setSavedStatus(result.selectionStatus);
        }
      })
      .catch(() => undefined);
    return () => { active = false; };
  }, [sessionId]);

  const acceptCandidate = useCallback(async (time: string) => {
    if (!candidateResult || acceptingTime) return;
    setError("");
    setAcceptingTime(time);
    try {
      const response = await fetch("/api/rectification/agent", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          action: "accept_candidate",
          sessionId,
          resultId: candidateResult.resultId,
          time,
        }),
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok || payload?.ok !== true) throw new Error(payload?.message || payload?.error || "暂时无法采用该候选时间");
      const status = payload.status === "confirmed" ? "confirmed" : "accepted";
      setCandidateResult((current) => current ? { ...current, selectedTime: payload.saved_time, selectionStatus: status } : current);
      setSavedTime(payload.saved_time);
      setSavedStatus(status);
      onSaved?.(payload.saved_time, status);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "暂时无法采用该候选时间");
    } finally {
      setAcceptingTime(null);
    }
  }, [acceptingTime, candidateResult, onSaved, sessionId]);

  useEffect(() => {
    if (initialMessages.length > 0 || openingStarted.current) return;
    openingStarted.current = true;
    void send({ action: "opening" }, false);
  }, [initialMessages.length, send]);

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
          {candidateResult?.selectionAllowed && candidateResult.candidates.length > 0 && (
            <section className="rectification-candidates" aria-label="生时校正候选时间">
              <div className="rectification-candidates-heading">
                <strong>{candidateResult.confirmationAllowed ? "已通过确认门" : "请选择校正采用时间"}</strong>
                <span>相对支持度仅用于本次候选比较，不是统计概率。</span>
              </div>
              <div className="rectification-candidate-list">
                {candidateResult.candidates.map((candidate) => {
                  const selected = candidateResult.selectedTime === candidate.time;
                  return (
                    <div className={`rectification-candidate${selected ? " is-selected" : ""}`} key={`${candidateResult.resultId}-${candidate.time}`}>
                      <div>
                        <strong>{candidate.time}</strong>
                        <span>相对支持度 {candidate.relative_support}%</span>
                      </div>
                      <div className="rectification-support" aria-hidden="true"><i style={{ width: `${candidate.relative_support}%` }} /></div>
                      <Button
                        type="button"
                        variant={selected ? "secondary" : "outline"}
                        disabled={Boolean(candidateResult.selectedTime) || Boolean(acceptingTime)}
                        onClick={() => void acceptCandidate(candidate.time)}
                      >
                        {selected ? "已采用" : acceptingTime === candidate.time ? "保存中…" : `采用 ${candidate.time}`}
                      </Button>
                    </div>
                  );
                })}
              </div>
            </section>
          )}
          {savedTime && (
            <p className="rectification-saved" role="status">
              {savedStatus === "confirmed" ? "已确认校正时间" : "校正采用时间"}：{savedTime}。后续排盘将使用该时间。
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
