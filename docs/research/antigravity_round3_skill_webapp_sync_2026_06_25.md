# Antigravity AI Skill 与网页/app 一致性审计 (Round 3)

## 1. 对标
在 AI Prompt 包装与上下文承载设计上，本项目走在了传统竞品（如 VedAstro 的单纯数据拼接或 AstroSage 的弱 AI）之前。通过明确的 `ai_prompt_pack` 对象规范，前端和 AI Skill 可以无缝同步获取“带置信度和原始证据截断”的 RAG 上下文，确保了回答的确定性。

## 2. 开源参考
参考 VedAstro.Python 的调用说明和开源生态中的其他项目，许多系统在扩展 AI 能力时往往陷入“硬拼接”困局，没有规范的数据证据载体。本次同步审计证实，Codex 设计的 `ai_prompt_pack` 及 `evidence_snapshot` 在避免过度推理及同步前端逻辑上表现优异，没有走老路。

## 3. Bug
本次审计涵盖 `SKILL.md` 及前端相关 AI 获取逻辑，发现前期记录的问题已被 Codex 悉数修复，具体验证结果如下：

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|
| **P1** | `SKILL.md` | ~135 | 曾缺乏对 `ai_prompt_pack` 与 `ayanamsa` 显示规范的强制性约束。 | N/A | **已被 Codex 修复。** Skill 文档第 135 行及以后已明确要求优先读取 `birth_info.ayanamsa_name/display`，并强制消费 `evidence_snapshot` 和 `retrieval_plan`。 |
| **P1** | `SKILL.md` | ~167 | 曾夸大 Shadbala/Dasha 绝对值对齐状况，宣称为“已同步”。 | N/A | **已被 Codex 修复。** 第 167 行已明确退回防御性话术：“主输出为 absolute Rupa 分量求和，可作为内部相对强弱参考，但不得声称已完成外部绝对值校准。” |
| **P1** | `jyotish-app/api-bridge.js` <br/> `jyotish-app/ai-chat.js` | ~349, <br/> ~284 | 曾经有旧版 prompt 硬编码拼接绕过后端 `ai_prompt_pack` 的逻辑。 | N/A | **已被 Codex 修复。** 代码已更新为优先检查 `cd.ai_prompt_pack?.prompt_zh`，仅当该值不存在时才执行兼容降级。 |

**一致性审计结论：`SKILL.md` 的规范描述已与网页端及 API 引擎产出的能力完全对齐。同时也并未发现擅自持久化、输出或跨越隐私边界传播用户输入出生资料的逻辑。**
