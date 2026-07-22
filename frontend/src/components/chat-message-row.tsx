import { AgentActivityStatus } from "@/components/agent-activity-status";
import { ChatMessageContent } from "@/components/chat-message-content";
import type { ChatMessageView } from "@/lib/chat-message-view";

export function AgentAvatar() {
  return <span className="agent-avatar" aria-hidden="true" />;
}

export function ChatMessageRow({ message }: { readonly message: ChatMessageView }) {
  const assistantLabel = message.state === "thinking"
    ? "Jyotisha 正在分析"
    : message.state === "streaming"
      ? "Jyotisha 正在回答"
      : "Jyotisha";

  return (
    <article
      className={`message message-${message.role}`}
      aria-label={message.role === "assistant" ? assistantLabel : "你"}
    >
      {message.role === "assistant" && <AgentAvatar />}
      <div className="message-content">
        <div className="message-bubble">
          {message.role === "assistant" ? (
            message.state === "thinking"
              ? <AgentActivityStatus state="working" label="正在核对星盘信息…" />
              : <>
                {message.state === "streaming" && <AgentActivityStatus state="composing" />}
                <ChatMessageContent text={message.text} />
              </>
          ) : <p>{message.text}</p>}
        </div>
      </div>
    </article>
  );
}
