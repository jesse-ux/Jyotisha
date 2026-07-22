import type { ConsultationTheme } from "./consultation-workflow-request";

export type GuidedJyotishTopic = {
  id: ConsultationTheme;
  label: string;
  prompt: string;
  strictWorkflowRoute: string;
  evidencePreview: string[];
  confidenceCap: "low" | "medium";
  claimBoundary: string;
};

export const defaultGuidedJyotishTopics: GuidedJyotishTopic[] = [
  {
    id: "career",
    label: "事业",
    prompt: "未来一年，事业和收入该关注什么？",
    strictWorkflowRoute: "career",
    evidencePreview: ["D1", "D10", "A10", "Vimshottari", "Narayana", "Transit"],
    confidenceCap: "medium",
    claimBoundary: "输出职业结构与阶段判断；具体日/月只作为候选窗口。",
  },
  {
    id: "marriage",
    label: "关系",
    prompt: "我的关系模式是什么？",
    strictWorkflowRoute: "marriage",
    evidencePreview: ["D1", "D9", "7宫", "DK", "UL", "Vimshottari", "Narayana"],
    confidenceCap: "medium",
    claimBoundary: "输出关系模式与宽窗口；不承诺某日必然发生事件。",
  },
  {
    id: "wealth",
    label: "财富",
    prompt: "我的财富增长方式和风险点是什么？",
    strictWorkflowRoute: "wealth",
    evidencePreview: ["D1", "D2", "D11", "2/11宫", "财富 Yoga", "Ashtakavarga"],
    confidenceCap: "medium",
    claimBoundary: "输出财富结构和风险类型；不替代投资建议。",
  },
  {
    id: "timing",
    label: "时运",
    prompt: "未来哪些阶段值得把握？",
    strictWorkflowRoute: "timing",
    evidencePreview: ["Dasha", "Narayana", "Transit", "Varga"],
    confidenceCap: "low",
    claimBoundary: "精确月/日仍是探索性候选，未通过独立 holdout 前不升级。",
  },
];
