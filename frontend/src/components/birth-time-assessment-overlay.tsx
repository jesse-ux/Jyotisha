import { AppLoadingIndicator } from "./app-loading-indicator.tsx";

export type BirthTimeAssessmentPhase = "saving_profile" | "assessing" | "entering_home";

const progressCopy = {
  saving_profile: {
    title: "正在保存出生资料",
    detail: "已保留你刚才的选择，马上开始生成生时评估。",
  },
  assessing: {
    title: "正在生成生时评估",
    detail: "正在读取已有资料并准备下一步，不需要重复操作。",
  },
  entering_home: {
    title: "正在进入首页",
    detail: "出生资料已保存，正在为你准备首页。",
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
      <AppLoadingIndicator
        className="birth-time-assessment-progress"
        title={copy.title}
        detail={copy.detail}
      />
    </div>
  );
}
