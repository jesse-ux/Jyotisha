export const consultationThemeValues = ["career", "marriage", "wealth", "timing", "general"] as const;

export type ConsultationTheme = typeof consultationThemeValues[number];

export type ConsultationWorkflowRoute =
  | "career"
  | "marriage"
  | "wealth"
  | "timing"
  | "rectification"
  | "prashna"
  | "general";

type WorkflowProjection = {
  question: string;
  themes: readonly ("career" | "marriage" | "wealth")[];
  strictWorkflowRoute: ConsultationWorkflowRoute;
  requiredLayers: readonly string[];
  claimBoundary: string;
};

const routeRequirements: Record<ConsultationTheme, Omit<WorkflowProjection, "question"> & { prefix?: string }> = {
  career: {
    themes: ["career"],
    strictWorkflowRoute: "career",
    requiredLayers: ["D1", "D10", "10th house/lord", "A10", "AmK", "Vimshottari", "Narayana", "Transit"],
    claimBoundary: "career_direction_and_broad_timing_only",
  },
  marriage: {
    themes: ["marriage"],
    strictWorkflowRoute: "marriage",
    requiredLayers: ["D1", "D9", "7th house/lord", "Venus/Jupiter", "DK", "UL", "A7", "Vimshottari", "Narayana", "Transit"],
    claimBoundary: "relationship_pattern_and_broad_window_only",
  },
  wealth: {
    themes: ["wealth"],
    strictWorkflowRoute: "wealth",
    requiredLayers: ["D1", "D2", "D11", "2nd/11th/9th/5th houses", "Wealth Yogas", "Ashtakavarga", "Dasha"],
    claimBoundary: "wealth_structure_not_financial_advice",
  },
  timing: {
    themes: ["career"],
    strictWorkflowRoute: "timing",
    requiredLayers: ["Vimshottari", "Narayana", "Transit", "Varga", "negative holdout gate"],
    claimBoundary: "candidate_day_month_window_only_until_holdout_passes",
    prefix: "应期与阶段问题：",
  },
  general: {
    themes: ["career", "marriage", "wealth"],
    strictWorkflowRoute: "general",
    requiredLayers: ["D1", "D9", "D10", "D2", "Dasha", "Narayana", "Transit", "Functional Benefic/Malefic"],
    claimBoundary: "multi_domain_summary_with_missing_layers_disclosed",
  },
};

export function projectConsultationWorkflowRequest(question: string, theme: ConsultationTheme) {
  const requirement = routeRequirements[theme];
  return {
    question: `${requirement.prefix ?? ""}${question}`,
    themes: requirement.themes,
    strictWorkflowRoute: requirement.strictWorkflowRoute,
    requiredLayers: requirement.requiredLayers,
    claimBoundary: requirement.claimBoundary,
  } satisfies WorkflowProjection;
}
