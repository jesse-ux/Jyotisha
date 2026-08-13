"use client";

import { useGSAP } from "@gsap/react";
import { gsap } from "gsap";
import { useRef } from "react";

import { AgentActivityStatus } from "@/components/agent-activity-status";
import { ChatMessageContent } from "@/components/chat-message-content";
import type { ChatMessageView } from "@/lib/chat-message-view";

gsap.registerPlugin(useGSAP);

export function AgentAvatar() {
  return <span className="agent-avatar" aria-hidden="true" />;
}

export function ChatMessageRow({ message }: { readonly message: ChatMessageView }) {
  const messageRow = useRef<HTMLElement>(null);
  const assistantLabel = message.state === "thinking"
    ? "Jyotisha 正在分析"
    : message.state === "streaming"
      ? "Jyotisha 正在回答"
      : "Jyotisha";

  useGSAP(() => {
    if (!messageRow.current) return;
    const motion = gsap.matchMedia();
    motion.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.fromTo(messageRow.current, {
        autoAlpha: 0,
        y: message.role === "user" ? 8 : 12,
      }, {
        autoAlpha: 1,
        clearProps: "opacity,transform,visibility",
        duration: 0.18,
        ease: "cubic-bezier(.22, 1, .36, 1)",
        y: 0,
      });
    });
    return () => motion.revert();
  }, { scope: messageRow });

  return (
    <article
      ref={messageRow}
      className={`message message-${message.role}`}
      aria-label={message.role === "assistant" ? assistantLabel : "你"}
    >
      {message.role === "assistant" && <AgentAvatar />}
      <div className="message-content">
        <div className="message-bubble">
          {message.role === "assistant" ? (
            <>
              {message.state !== "settled" && (
                <AgentActivityStatus
                  state={message.state === "thinking" ? "working" : "composing"}
                  label={message.state === "thinking" ? "正在核对星盘信息…" : undefined}
                />
              )}
              {message.text && <ChatMessageContent text={message.text} />}
            </>
          ) : <p>{message.text}</p>}
        </div>
      </div>
    </article>
  );
}
