import type { ChatMessage } from "./chat-message-view";

export function consultationReportMarkdown(input: {
  title: string;
  messages: readonly ChatMessage[];
}) {
  const latestAssistant = [...input.messages].reverse().find((message) => message.role === "assistant");
  const evidence = latestAssistant?.workflowReceipt;
  return [
    `# ${input.title}`,
    "",
    "## 最新回答",
    latestAssistant?.text || "暂无回答。",
    "",
    "## Claim boundary",
    `technique_truth: ${latestAssistant?.techniqueTruth || "unknown"}`,
    evidence ? `workflow_route: ${evidence.route}` : "workflow_route: unknown",
    evidence ? `workflow_status: ${evidence.status}` : "workflow_status: unknown",
    evidence ? `precise_timing: ${evidence.preciseTiming}` : "precise_timing: unknown",
    evidence ? `missing_layers: ${evidence.missingLayers.join(" / ") || "none"}` : "missing_layers: unknown",
    "",
    "## Boundary",
    "本报告保留证据边界；未闭环内容不得包装成确定预测。",
  ].join("\n");
}
