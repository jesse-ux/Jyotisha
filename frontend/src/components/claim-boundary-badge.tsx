const boundaryCopy: Record<string, string> = {
  unknown: "证据边界未知",
  partial: "部分证据闭环",
  observation_only: "仅观察",
  blocked: "证据阻塞",
  reference_only: "仅参考",
};

export function ClaimBoundaryBadge({ status }: { readonly status?: string }) {
  const normalized = status?.trim() || "unknown";
  const label = boundaryCopy[normalized] ?? `证据状态：${normalized}`;
  return <p className="claim-boundary-badge">{label} · 不把未闭环内容包装成确定预测。</p>;
}
