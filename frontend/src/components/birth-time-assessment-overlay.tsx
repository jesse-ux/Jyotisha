export type BirthTimeAssessmentPhase = "saving_profile" | "assessing";

const progressCopy = {
  saving_profile: {
    title: "正在保存出生资料",
    detail: "已保留你刚才的选择，马上开始生成生时评估。",
  },
  assessing: {
    title: "正在生成生时评估",
    detail: "正在读取已有资料并准备下一步，不需要重复操作。",
  },
} as const satisfies Record<BirthTimeAssessmentPhase, { readonly title: string; readonly detail: string }>;

export function BirthTimeAssessmentOverlay({ phase }: { readonly phase: BirthTimeAssessmentPhase | null }) {
  if (phase === null) return null;
  const copy = progressCopy[phase];

  return (
    <div
      className="birth-time-assessment-overlay"
      data-phase={phase}
      role="status"
      aria-live="polite"
    >
      <div className="birth-time-assessment-progress">
        <div className="app-loading-symbol" aria-hidden="true">
          <span className="app-loading-orbit" />
          <span className="app-loading-mark" />
        </div>
        <strong>{copy.title}</strong>
        <span>{copy.detail}</span>
      </div>
    </div>
  );
}
