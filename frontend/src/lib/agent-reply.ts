export type ReplyTheme = "career" | "marriage" | "timing" | "general";

const fallbackSuggestions: Record<ReplyTheme, readonly [string, string, string]> = {
  career: ["我更适合怎样的职业路径？", "未来一年事业上要避开什么？", "我该如何发挥自己的优势？"],
  marriage: ["我在关系里容易重复什么模式？", "怎样的伴侣更适合我？", "未来一年关系上要注意什么？"],
  timing: ["接下来最值得把握的阶段是什么？", "哪些时期更适合主动行动？", "我现在应该优先准备什么？"],
  general: ["未来一年，事业和收入该关注什么？", "我的关系模式是什么？", "未来哪些阶段值得把握？"],
};

function readSuggestions(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return [...new Set(value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.replace(/\s+/g, " ").trim().slice(0, 80))
    .filter(Boolean))].slice(0, 3);
}

function readTitle(value: string): string | undefined {
  const title = value.replace(/\s+/g, " ").trim();
  if (!title || /[\d\p{P}\p{S}]/u.test(title)) return undefined;
  if (/\p{Script=Han}/u.test(title)) {
    const length = Array.from(title.replace(/\s/g, "")).length;
    return length >= 6 && length <= 14 ? title : undefined;
  }
  const words = title.split(" ").filter(Boolean);
  return words.length >= 3 && words.length <= 7 && title.length <= 64 ? title : undefined;
}

export function parseAgentReply(value: string, theme: ReplyTheme) {
  let suggestions: string[] = [];
  let title: string | undefined;
  const withoutSuggestions = value.replace(/<!--AYANAM_SUGGESTIONS:(\[[\s\S]*?\])-->/g, (_, json: string) => {
    try {
      suggestions = readSuggestions(JSON.parse(json));
    } catch {
      suggestions = [];
    }
    return "";
  });
  const text = withoutSuggestions.replace(/<!--AYANAM_TITLE:([\s\S]*?)-->/g, (_, rawTitle: string) => {
    title = readTitle(rawTitle);
    return "";
  }).replace(/<!--AYANAM_[\s\S]*$/, "").trim();

  return {
    text,
    suggestions: suggestions.length === 3 ? suggestions : [...fallbackSuggestions[theme]],
    title,
  };
}

export function resolveSessionTitle(question: string, modelTitle?: string): string {
  if (modelTitle && modelTitle !== "一般占星咨询") return modelTitle;
  const normalized = question.replace(/\s+/g, " ").trim().replace(/[？?！!。．，,；;：:]+$/u, "");
  if (!normalized) return "新对话";
  const characters = Array.from(normalized);
  return characters.length > 14 ? `${characters.slice(0, 14).join("")}…` : normalized;
}
