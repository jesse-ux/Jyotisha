# Skill Sync Audit (2026-06-25)

## 审计目标
比对现有的 `SKILL.md` 能力描述与 `scripts/jyotish_engine.py full-reading` 底层输出，审查哪些核心能力在 Skill/Prompt 层面发生了脱节。

## 审计发现

### 1. Multi-Ayanamsa 能力感知缺失
- **现状**: 底层引擎与 API 已经支持通过 `--ayanamsa` 参数计算，并在 `birth_info` 中吐出了使用的岁差（如 Raman、KP 等）。但 `SKILL.md` 中完全没有关于 Ayanamsa 切换的任何指令或感知逻辑。
- **影响**: AI 在执行解盘时，可能会武断地假定用户是标准的 Lahiri 岁差，忽略了处理其他岁差制式下的星座漂移和边界条件。

### 2. ai_prompt_pack 未被使用
- **现状**: 引擎 `full-reading` 目前输出了包含高质量上下文的 `ai_prompt_pack` 结构（含 `prompt_zh`, `evidence_snapshot`, `retrieval_plan` 等字段）。但 `SKILL.md` 中完全没有指导 AI 优先消费这个字段作为 RAG 知识源的说明。
- **影响**: AI 可能还在试图从巨大的、无结构差异的 JSON 树中自行检索，导致计算成本增加并有可能遗漏核心 Yoga / Shadbala 等重要标记。

### 3. Dasha/Shadbala 校准状态表述滞后
- **现状**: `SKILL.md` 提到“Shadbala absolute Rupa ... 已同步”，但未明确阐述 Shadbala 的外部校准状态。实际上，当前的 Oracle json 中填充的是测试结构数据（标记为 `component_targets_sample_only` 或 `local_baseline`），校准仍在“补充外部绝对值 oracle”的过程中。
- **影响**: 这属于“夸大宣称”，AI 需要明白当前的 Shadbala 依然是结构测试期，不能直接宣称“百分之百”符合 JHora 精度。

## 结论建议
`SKILL.md` 需要进行一次大幅度的 Prompt Engineering 升级：
1. 增加获取并验证 `ai_prompt_pack` 的流程步骤。
2. 告知 AI 如何在有岁差争议的落位边缘，利用 `birth_info.ayanamsa_name` 进行澄清。
3. 修改校准状态的误导性词汇。
