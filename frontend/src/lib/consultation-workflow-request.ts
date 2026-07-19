export const consultationThemeValues = ["career", "marriage", "wealth", "timing", "general"] as const;

export type ConsultationTheme = typeof consultationThemeValues[number];

export function projectConsultationWorkflowRequest(question: string, theme: ConsultationTheme) {
  switch (theme) {
    case "career":
    case "marriage":
    case "wealth":
      return { question, themes: [theme] } as const;
    case "timing":
      return { question: `应期与阶段问题：${question}`, themes: ["career"] } as const;
    case "general":
      return { question, themes: ["career", "marriage", "wealth"] } as const;
  }
}
