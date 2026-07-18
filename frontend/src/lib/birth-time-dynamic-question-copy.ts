import { createHash } from "node:crypto";
import type { CandidateDifferencePacket } from "./birth-time-dynamic-choice-internal.ts";

const timeOfBirthPattern = /(?:^|[^\d])(?:[01]?\d|2[0-3])\s*[:：]\s*[0-5]\d(?:$|[^\d])/;
const confidencePattern = /置信(?:度)?|可信度|准确率|准确度|概率最高|把握(?:最高|更高)/;
const supportPattern = /(?:更|最)?支持(?:第[一二三四]组|哪一组|.*结果|.*候选)|(?:候选|出生).*(?:支持|排除|更符合|更接近)/;
const controlPattern = /评分|得分|权重|算法|模型|证据分区|分区标识|停止提问|结束评估|应用(?:到)?排盘|更新排盘|系统(?:会|将)|直接锁定|锁定(?:答案|结果|时间)|最终答案/;
const instructionPattern = /忽略|无视|不要遵守|提示词|系统提示|开发者指令|遵循|服从|你(?:必须|应当|需要)|务必|执行(?:以上|以下|下列|这|该|内容)|把问题改成|改写问题|替换问题|请(?:选择|返回|输出)|按照.*(?:指令|规则)|回答成|输出为/;
const birthTimeClaimPattern = /出生(?:时间|时刻|分钟|几点)|生时|候选(?:时间|分钟|答案)/;
const groundingTerms = [
  "升学", "转学", "学习", "搬家", "离乡", "居住", "关系",
  "工作", "职业", "身份", "健康", "压力", "生活",
] as const;
const experiencePattern = /变化|转变|进入|结束|发生|经历|开始|离开|升学|转学|搬家|离乡|压力/;

export function dynamicPublicCopyIsSafe(value: string, question: boolean): boolean {
  const normalized = value.normalize("NFKC").trim();
  if (!/[\u3400-\u9fff]/u.test(normalized) || /[A-Za-z]/.test(normalized)) return false;
  if (timeOfBirthPattern.test(normalized) || birthTimeClaimPattern.test(normalized)) return false;
  if (confidencePattern.test(normalized) || supportPattern.test(normalized)) return false;
  if (controlPattern.test(normalized)) return false;
  return !question || (normalized.match(/[？?]/g) ?? []).length === 1;
}

export function dynamicQuestionIsGrounded(prompt: string, neutralContext: string): boolean {
  const terms = groundingTerms.filter((term) => neutralContext.includes(term));
  return experiencePattern.test(prompt)
    && terms.length > 0
    && terms.some((term) => prompt.includes(term));
}

function safeUnmatchedNote(value: string | null): string | null {
  const normalized = value?.normalize("NFKC").trim() || null;
  if (normalized === null) return null;
  if (normalized.length > 240) return null;
  if (
    timeOfBirthPattern.test(normalized)
    || birthTimeClaimPattern.test(normalized)
    || confidencePattern.test(normalized)
    || supportPattern.test(normalized)
    || controlPattern.test(normalized)
    || instructionPattern.test(normalized)
  ) return null;
  return normalized;
}

export function modelSafeDynamicQuestionPrompt(
  packet: CandidateDifferencePacket,
  unmatchedNote: string | null,
): string {
  const note = safeUnmatchedNote(unmatchedNote);
  return JSON.stringify({
    task: "generate_dynamic_choice_question",
    opportunities: packet.opportunities.map((opportunity) => ({
      opportunityId: opportunity.opportunityId,
      dimensionCode: opportunity.dimensionCode,
      neutralContext: opportunity.neutralContext,
      partitions: opportunity.partitions.map((partition) => ({
        partitionId: partition.partitionId,
        descriptor: partition.descriptor,
        fallbackLabel: partition.fallbackLabel,
      })),
    })),
    unmatchedNote: note === null ? null : {
      trust: "untrusted_user_evidence",
      quotedText: note,
    },
  });
}

function normalizeSemanticCopy(value: string): string {
  return value.normalize("NFKC").trim().replace(/\s+/g, "");
}

export function dynamicQuestionSemanticFingerprint(output: {
  readonly prompt: string;
  readonly options: readonly { readonly label: string }[];
}): string {
  const semantics = {
    prompt: normalizeSemanticCopy(output.prompt),
    options: output.options.map((option) => normalizeSemanticCopy(option.label)),
  };
  return createHash("sha256")
    .update(`birth-time-dynamic-question-v1\n${JSON.stringify(semantics)}`, "utf8")
    .digest("hex");
}
