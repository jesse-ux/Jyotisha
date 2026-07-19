import { z } from "zod";

export const consultationEntrypointSchema = z.enum([
  "daily_starlanguage",
  "birth_time_rectification",
]);

export type ConsultationEntrypoint = z.infer<typeof consultationEntrypointSchema>;

type ConsultationQuestionInput = {
  readonly visibleQuestion: string;
  readonly entrypoint: ConsultationEntrypoint | undefined;
  readonly currentDate: string;
};

export type ResolvedConsultationQuestion =
  | { readonly kind: "plain"; readonly modelQuestion: string }
  | { readonly kind: "expanded"; readonly modelQuestion: string };

export function resolveConsultationQuestion(
  input: ConsultationQuestionInput,
): ResolvedConsultationQuestion {
  switch (input.entrypoint) {
    case undefined:
      return { kind: "plain", modelQuestion: input.visibleQuestion };
    case "daily_starlanguage":
      return {
        kind: "expanded",
        modelQuestion: [
          `请结合已校验的星盘资料，深入解读 ${input.currentDate} 的今日主题。`,
          "请说明今日趋势、适合推进的事、需要避开的事，以及一个可以立即执行的行动建议。",
          "这是探索性日提示，不是确定预测；精确事件日期只能标为候选触发，不能包装成必然结论。",
        ].join("\n"),
      };
    case "birth_time_rectification":
      return {
        kind: "expanded",
        modelQuestion: [
          "请基于已校验的出生资料继续进行生时校正辅助。",
          "先判断现有证据与候选结果，再说明最有区分度的下一步；需要补充信息时优先给用户可点击、容易回答的选项。",
          "候选时间必须标为待验证，不能声称是出生记录中的确定分钟，也不能在没有新证据时循环重启相同流程。",
        ].join("\n"),
      };
    default: {
      const exhaustive: never = input.entrypoint;
      return exhaustive;
    }
  }
}
