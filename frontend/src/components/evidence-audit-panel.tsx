type AuditRow = {
  label: string;
  status: "required" | "partial" | "blocked";
  boundary: string;
};

const defaultAuditRows: AuditRow[] = [
  { label: "D1 / Natal", status: "required", boundary: "基础命盘层" },
  { label: "Varga: D9 / D10 / D2 / D11", status: "required", boundary: "按问题域调用，不混用" },
  { label: "Vimshottari Dasha", status: "required", boundary: "阶段证据之一" },
  { label: "Narayana Dasha", status: "required", boundary: "应期/校时必须交叉" },
  { label: "Transit / Gochara", status: "partial", boundary: "精确日/月仍需 holdout" },
  { label: "Shadbala / Ashtakavarga", status: "partial", boundary: "组件 parity 未全闭环" },
  { label: "Functional Benefic/Malefic", status: "required", boundary: "不能只看自然吉凶" },
  { label: "MEVG / Real Case Calibration", status: "blocked", boundary: "外部校准不足时降级" },
];

export function EvidenceAuditPanel({ claimStatus }: { readonly claimStatus?: string }) {
  return (
    <details className="evidence-audit-panel">
      <summary>证据链摘要 · {claimStatus || "unknown"}</summary>
      <div className="evidence-audit-table" role="table" aria-label="Technique Audit Table">
        {defaultAuditRows.map((row) => (
          <div className="evidence-audit-row" role="row" key={row.label}>
            <span role="cell">{row.label}</span>
            <b role="cell" data-status={row.status}>{row.status}</b>
            <small role="cell">{row.boundary}</small>
          </div>
        ))}
      </div>
    </details>
  );
}
