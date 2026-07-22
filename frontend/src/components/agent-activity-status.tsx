import { ThinkingOrb, type OrbState } from "thinking-orbs";

const labels = {
  working: "正在处理任务…",
  searching: "正在搜索相关信息…",
  solving: "正在分析问题…",
  listening: "正在聆听…",
  composing: "正在组织回答…",
  shaping: "正在生成结果…",
} as const satisfies Record<OrbState, string>;

export function AgentActivityStatus({
  state,
  label = labels[state],
}: Readonly<{
  state: OrbState;
  label?: string;
}>) {
  return (
    <div className="agent-activity-status" role="status">
      <ThinkingOrb aria-hidden="true" state={state} size={20} />
      <span>{label}</span>
    </div>
  );
}
