import { ChatMessageContent } from "@/components/chat-message-content";
import { ClaimBoundaryBadge } from "@/components/claim-boundary-badge";
import { EvidenceAuditPanel } from "@/components/evidence-audit-panel";
import type { ChatMessageView } from "@/lib/chat-message-view";
import { consultationReportMarkdown, downloadMarkdownReport } from "@/lib/consultation-report-export";

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
              ? <div className="thinking"><i /><i /><i /></div>
              : <><ClaimBoundaryBadge status={message.techniqueTruth} /><EvidenceAuditPanel claimStatus={message.techniqueTruth} workflowReceipt={message.workflowReceipt} /><ChatMessageContent text={message.text} /><button className="report-download-button" type="button" onClick={() => downloadMarkdownReport("Jyotisha 咨询报告", consultationReportMarkdown({ title: "Jyotisha 咨询报告", messages: [message] }))}>下载本次报告</button></>
          ) : <p>{message.text}</p>}
        </div>
      </div>
    </article>
  );
}
