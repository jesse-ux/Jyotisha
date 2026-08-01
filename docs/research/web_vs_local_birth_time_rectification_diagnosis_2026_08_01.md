# Web 生时纠正 vs 本地 Claude Code：差异诊断与改进方案

> 日期：2026-08-01
> 状态：诊断完成；改进方案第 4 节"完整 MVP"已实施（见第 7 节）
> 范围：`jyotish-vedic-astrology` skill 方法论层 vs Web `skills/birth-time-rectification` 受限产品层

## 结论摘要

Web（staging）上用户感受到的"生时纠正交互僵硬、问题像硬编码模板"，**不是 bug，而是两种刻意不同的架构**：

- **本地 Claude Code**：LLM 是**主分析师**，走 `jyotish-vedic-astrology` skill 的完整方法论，可自由多轮提问、运行脚本、交叉验证，最终产出精确出生分钟。
- **Web（Mastra）**：LLM 是**被约束的叙述者**，走 `skills/birth-time-rectification/SKILL.md`（36 行受限证据工作流）。服务端 Python 引擎 + TS 状态机拥有全部计算（候选扫描/评分/诊断/事件 ID/策略门控），LLM 只能在服务端预建的问题机会里选一个、再渲染短中文回复，永不确认单一分钟。

staging 前端实际挂载的是 **v4 rectification** 入口（`RectificationV4Panel` → `/api/rectification/v4/*`）。"硬编码感"主要来自服务端模板问题生成器 `opportunity-builder.ts`，与 v4/v5 模式切换无关。

---

## 1. 两个系统的架构对比

| 维度 | 本地 Claude Code | Web（Mastra v4 rectification） |
|---|---|---|
| 使用的 skill | `jyotish-vedic-astrology`（仓库根 `SKILL.md`，712 行，版本 6.9.14） | `skills/birth-time-rectification/SKILL.md`（36 行） |
| skill 目录结构 | symlink 指向根目录 `SKILL.md` + `references/`（100+ 方法论文档）+ `scripts/`（`jyotish_engine.py` 37 子命令）+ `assets/` | 36 行 SKILL.md + 6 个契约文件在 `skills/birth-time-rectification/references/` + `assets/rectification-capability-matrix.json` |
| 方法论 | 8 大方法（Dasha+Transit、D9 Navamsa、D10 Dasamsa、六亲、外表体质、身体缺陷、职业判断、卜卦【AI 暂不支持】）；五阶段流程（收集→±30min→±15min→事件验证→D9/D10 收口到 ±5min→报告）；决策树权重 Dasha 40% / D9+D10 35% / 专题层 15% / Nakshatra Pada 10% | 受限证据工作流：服务端扫描候选时间簇→评分→生成高信息量机会；agent 每轮只问一个自然问题；输出候选区间而非确定时间 |
| LLM 角色 | 主分析师，自由推理 | 被约束的叙述者（reasoner 选机会 / renderer 渲染） |
| 计算归属 | LLM 驱动 + `scripts/` 脚本 + 外部 oracle（PyJHora/VedAstro/jyotishganit） | 服务端 Python 引擎 + TS 状态机全拥有 |
| 输出 | 验证后的出生分钟（±5min） | 候选区间（`profiles.active_birth_time` 永不直接写入） |
| 错误处理 | 交互式纠错 | 幂等重放（action receipt + fingerprint）、确定性回退 |

**两者的关系**：`jyotish-vedic-astrology` skill 内部同时定义了这两层——方法论层（`references/birth-time-rectification-advanced.md`）和受限产品工作流层（独立的 `skills/birth-time-rectification/`）。Web 端刻意只暴露受限产品层。

---

## 2. 为什么 Web 无法复刻本地交互（6 个根源）

### 2.1 权威模型相反（设计边界，不是 bug）

`skills/birth-time-rectification/SKILL.md` 硬边界原文：

> - The server owns candidate scanning, scores, diagnostics, event IDs, and policy gates.
> - The agent may select one server-provided opportunity or request one server-provided diagnostic.
> - Never invent candidate times, scores, event IDs, dates, techniques, or tool inputs.
> - Never confirm a single minute or write `profiles.active_birth_time`.

这是一整套产品决策：**计费**（`billing.ts` reserve/complete/release）、**不暴露内部分数**（用户只能看到"候选区间"而非权重/评分）、**可靠性**（服务端计算确定性可审计，LLM 只做叙述）、**truth-overlay 合规**（`references/oracle/rectification_technique_usage_audit_2026_07_19.json` 把 D9/D10/D60 等标为"敏感度证据不是证明"）。本地 Claude Code 没有这些约束，所以能做完整方法论。

### 2.2 问题是服务端模板（"硬编码感"最强处）

`frontend/src/lib/rectification-agent/opportunity-builder.ts`：

- **固定模板文案**：`prompt` 字段全部是写死的句子，例如——
  - `clarify_event_subject`："你刚才提到"X"，这件事主要发生在你本人，还是家人或伴侣身上？"
  - `refine_event_date`："关于"X"，你还记得更具体的月份或日期吗？不确定也可以只说大概范围。"
  - `ask_new_event` 各领域：career/relationship/health_pressure 等各一句。
- **硬编码 utility 公式**（L24-30）：`.35*expectedInformationGain + .20*dateSensitivity + .15*candidateSplitRelevance + .10*domainCoverageGain + .10*recallEase + .10*novelty + routingValue[kind] - repetitionPenalty - privacyCost`，其中 `routingValue` 也是写死的（L14-22）。
- reasoner（`reasoner-agent.ts`）只按 `opportunityId` 选一个机会，**从不用自己的话提问**。

> v3 对话式（`/api/birth-time-conversation`）的 `narrative-agent.ts` 已带 `freeConversation` 设置、允许 agent 自由措辞——但 v3 后端未接入当前 UI 面板。

### 2.3 每轮只问一个问题

skill turn strategy："Ask one natural question only"。`reasoner-agent.ts` 的决策被 `rectificationDecisionSchema` 严格约束，`maxToolCalls` 默认 1、最多一次 `run_rectification_diagnostics` 工具调用，然后必须返回终态动作。本地 Claude Code 是自由多轮对话。

### 2.4 Mastra skill 懒加载

`@mastra/core`（v1.50.1）的 skill 机制：`skills: [skillPath]` 只把 skill **元数据**（name/description，`<available_skills>` 块）注入系统提示；完整 `SKILL.md` 要模型主动调 `skill` 工具才在对话中加载（`node_modules/@mastra/core/dist/` 的 `SkillsProcessor`）。deepseek 走 `structuredOutput` 路径时未必稳定触发 `skill` 工具 → LLM 实际可用的指令比预期少。

### 2.5 硬编码业务规则

- `references/rectification_policy.v1.json`：`minScoringEvents=1`、`minConfirmationEvents=4`、`minConfirmationDomains=3`、`maxExternalValidationWidthMinutes=15`、`maxConfirmationWidthMinutes=5`、`minConfirmationMarginPercent=20`、`maxPlateauRounds=2`。→ 必须凑够 ≥4 个事件、≥3 个领域，否则一直追问，造成"问卷感"。
- 时段区间（`orchestrator.ts` L565-594、`handler.ts` L426-451）：early_morning/morning/afternoon/evening/late_night；不确定性（医院 ±2min、家庭 5/10/15、约估 15/30/60）。
- 正则模式（`orchestrator.ts` L132-139）：方向切换词/不确定词/肯定否定词/相对日期词。
- 领域分类关键词表（`evidence-extractor.ts` L101-146）。
- 回退文案（`narrative-agent.ts` L639-651）。
- 模型 ID（`handler.ts` L831-832）：`deepseek-v4-pro` / `deepseek-v4-flash`。

### 2.6 渲染约束

- reasoner/renderer 都强制 `structuredOutput` JSON（`reasoner-agent.ts` L124、`renderer-agent.ts` L62）。
- renderer 还要 `enforceServerQuestion`（L38-40、L63）把服务端预建的 `exactQuestion` 强制覆盖进输出——LLM 措辞被服务端文案顶替。
- 模型为 deepseek 系列（非 Claude），对话自然度与指令遵循不同。

---

## 3. staging 入口确认

| 项 | 结论 | 证据 |
|---|---|---|
| 前端 UI | **v4 rectification**：`ConversationalBirthTimeRectification` 只是 `RectificationV4Panel` 的别名 | `components/conversational-birth-time-rectification.tsx:20` |
| API 入口 | `/api/rectification/v4/*` | `lib/rectification-v4/client.ts`（cases / active / answer / revise / accept-range / pause/resume/abandon） |
| v4 流程内部 | `runBoundedReasoner`（reasoner-agent.ts）+ `renderPublicTurn`（renderer-agent.ts），两者 `skills: [rectificationSkillPath]`（受限 36 行 skill） | `reasoner-agent.ts:115`、`renderer-agent.ts:16` |
| 模型 | `RECTIFICATION_ORCHESTRATION_MODEL_ID` / `RECTIFICATION_NARRATION_MODEL_ID`（未设则默认目录） | `case-service.ts:46-47` |
| v5 agent vs v4 legacy | 由部署宿主 `.env.staging` 的 `RECTIFICATION_AGENT_V5_ENABLED` / `RECTIFICATION_AGENT_V5_CANARY_PERCENT` / `RECTIFICATION_AGENT_V5_SHADOW` 决定（`feature-policy.ts`），仓库不可见；**两种模式都走同一套受限 skill + 模板问题** | `lib/rectification-agent/feature-policy.ts:26-39` |
| v3 对话式 | 按 rollout audience（paused/smoke_only/public）门控，**未接入当前 UI 面板** | `deploy/configure-staging-rectification-rollout.sh`、`components/rectification-v4-panel.tsx`（无 v3 引用） |
| 部署副本 | Dockerfile 把 `SKILL.md`/`assets`/`references`/`scripts`/`skills` 拷进 `/app/`，symlink 保留 | `deploy/railway-web.Dockerfile:18-22` |

> 注：`/api/health` 只上报 v3 的 rollout 状态（`rollout.conversationalRectificationV3.creationAudience`），不包含 v5 agent 的开关值，因此 v5 模式是否在 staging 开启需查部署宿主的 `.env.staging`。

---

## 4. 改进方案（在"服务端拥有计算"护栏内）

按侵入性从低到高排列，均为**建议**（本次未实施）。任何方案都不得把内部分数/权重/事件 ID 暴露给用户，不得确认单一分钟。

### 4.1 即时注入 skill 指令（低侵入，收益高）

- **改动**：把 36 行 `skills/birth-time-rectification/SKILL.md` 直接内联进 reasoner/renderer 的 `instructions`（`reasoner-agent.ts:117`、`renderer-agent.ts:17`），保留 `skills: [skillPath]` 作为能力来源。
- **效果**：消除 Mastra skill 懒加载不确定性——模型每轮都确定拥有"turn strategy + public language + 硬边界"指令。
- **风险**：低。指令与 skill 内容一致，只是从懒加载改为常驻。

### 4.2 LLM 起草问题 + 服务端 grounded 校验（中侵入，消除"模板感"核心）

- **改动**：`opportunity-builder.ts` 保留"选哪个机会"的服务端决策（kind/targetEventId/domain/utility），但把 `prompt` 从"必须原样使用"改为"话题约束"；reasoner 用自然语言起草问题文本；新增一个 grounding 校验（复用 `narrative-agent.ts` 的 grounding 思路）确认草稿：① 命中目标事件/领域 ② 不含内部分数/权重/事件 ID ③ 是单问。
- **效果**：问题随上下文自适应，消灭"你刚才提到X…"的模板感。
- **风险**：中。需要新增校验层与测试；reasoner 输出 schema 从"选 opportunityId"扩展为"选 opportunityId + 起草文本"。

### 4.3 自由对话回合（中侵入）

- **改动**：服务端没有待处理机会（`opportunities` 为空或全部低效用）时，允许 agent 走"自然回应"而非强制提问。可复用 v3 `narrative-agent.ts` 的 `freeConversation` / `questionsAreOptional` 提示词模式，让 renderer 生成 1-3 句自然中文 + 可选开放收尾。
- **效果**：不再每轮都是"选择题"，更像本地对话。
- **风险**：中。需防止发散、防止确认未验证分钟；收敛判定仍由服务端掌控。

### 4.4 渲染放宽（中侵入）

- **改动**：renderer 从 `structuredOutput` JSON 改为自然中文文本输出 + 事后校验（`enforceServerQuestion` 保留为兜底，仅当需要明确问题时强制服务端文案）。
- **效果**：回复更自然，减少 JSON 式僵硬措辞。
- **风险**：中。需新的文本校验（主题、长度、泄密扫描）。

### 4.5 模型目录加入 Claude（低侵入，可选）

- **改动**：`frontend/src/mastra/model.ts` 的模型目录加入 Claude（如 `claude-sonnet-5`），`RECTIFICATION_NARRATION_MODEL_ID` 指向它。
- **效果**：叙事/对话质量显著提升（deepseek 在结构化约束下更易模板化）。
- **风险**：低，纯配置；需确认供应商密钥与成本。

---

## 5. 不应改动（设计边界）

以下为 `birth-time-rectification` skill 与产品契约的硬性约束，**任何改进都不得触碰**：

1. 服务端拥有候选扫描、评分、诊断、事件 ID、策略门控。
2. 永不确认单一分钟；永不直接写 `profiles.active_birth_time`。
3. 候选区间只有确定性稳定门通过才对用户可见（`canAcceptRange`）。
4. 计费幂等（billing reserve/complete/release + action receipt 指纹重放）。
5. truth-overlay 强制降级：`reference_only`/`blocked`/`partial` 技法不得作为确定性结论（`references/oracle/skill_truth_overlay_2026_07_19.json`）。
6. 不暴露内部分数、权重、领域标签、工具载荷、agent 轨迹。

改进目标是让**叙述/提问的自然度**贴近本地，而不是让 Web 复刻本地的方法论深度——那需要把整条计算链路搬进 LLM 上下文，与现有产品架构冲突。

---

## 6. 附：关键文件索引

| 文件 | 作用 |
|---|---|
| `skills/birth-time-rectification/SKILL.md` | Web 端受限 skill（36 行硬边界） |
| `SKILL.md`（仓库根） | 本地完整 skill（712 行方法论，symlink 到 skill 目录） |
| `frontend/src/lib/rectification-agent/opportunity-builder.ts` | 服务端模板问题生成器（硬编码根源） |
| `frontend/src/lib/rectification-agent/reasoner-agent.ts` | v4/v5 reasoner（选机会 + diagnostic 工具） |
| `frontend/src/lib/rectification-agent/renderer-agent.ts` | v4/v5 renderer（渲染公开回合 + enforceServerQuestion） |
| `frontend/src/lib/rectification-agent/feature-policy.ts` | v4_legacy / v5_shadow / v5_agent 选择 |
| `frontend/src/lib/rectification-v4/case-service.ts` | 建 case、deployment_mode、模型 ID |
| `frontend/src/lib/rectification-v4/supabase-store.ts` | 持久化 deployment_mode/agent_mode |
| `frontend/src/lib/conversational-rectification/narrative-agent.ts` | v3 叙事 agent（freeConversation 参考实现） |
| `frontend/src/app/api/birth-time-conversation/handler.ts` | v3 handler（deepseek 模型 ID、流式） |
| `references/rectification_policy.v1.json` | 收敛门槛硬编码 |
| `deploy/configure-staging-rectification-rollout.sh` | staging rollout（paused/smoke_only/public） |
| `frontend/supabase/migrations/20260728020000_*.sql` | v5 列（deployment_mode/agent_mode/model id/version） |

---

## 7. 已实施：Agentic 生时纠正 MVP（2026-08-01）

按用户决策"完全复刻本地方法论"，实现了一个新的 **agentic 生时纠正**聊天流：LLM 挂载完整 `jyotish-vedic-astrology` skill，像本地 Claude Code 一样驱动方法论，通过引擎工具请求计算（而不是自己瞎算），自由多轮对话，最终经高 rigor 确认门 + 用户明确同意后写回 `profiles.active_birth_time`。

### 7.1 新增文件

| 文件 | 作用 |
|---|---|
| `frontend/src/mastra/rectification-tools.ts` | 7 个工具包 Python 引擎端点：`rectification-gate`（精度门）、`rectification-scan`（分钟敏感度扫描）、`rectification-score`（V5 矩阵评分）、`rectification-diagnostics`（鲁棒性诊断）、`rectification-candidate-features`（候选静态特征）、`rectification-confirm`（高 rigor 三引擎 parity 确认门）、`rectification-save-birth-time`（服务端双重校验后写 profile） |
| `frontend/src/mastra/agentic-rectification.ts` | agent 工厂：完整 skill + 工具 + 中文指令（方法论流程、truth overlay、保存门控） |
| `frontend/src/lib/rectification-agentic/session.ts` | 会话支持：加载 profile 出生字段、`applyConfirmedBirthTime` 调 service-role RPC 写回 |
| `frontend/src/app/api/rectification/agent/route.ts` | NDJSON 流式端点：认证 → profile → 计费 reserve → agent.stream → delta/done 事件 → settle |
| `frontend/src/components/rectification-agentic-chat.tsx` | 聊天面板：流式渲染、隐藏块解析（suggestions/title/保存哨兵）、错误处理 |
| `frontend/src/components/conversational-birth-time-rectification.tsx` | 入口智能切换：有进行中的 v4 case → v4 面板恢复；否则 → agentic 聊天 |
| `frontend/supabase/migrations/20260801000000_agentic_rectification_profile_write.sql` | `apply_agentic_rectification_birth_time` RPC（security definer，仅 service_role，含基线并发保护） |
| `frontend/tests/rectification-agentic-tools.test.ts` / `rectification-agentic-session.test.ts` | 12 个测试 |

### 7.2 安全门控（核心）

LLM 绝不能写任意分钟。`rectification-confirm` 只有在引擎高 rigor 门全过（≥4 事件、≥3 领域、宽度/边际阈值、三引擎 parity、外部 VedAstro 校验）返回 `confirmation_allowed=true` + 确认分钟时，才在会话闭包中设置 `confirmedGate`；`rectification-save-birth-time` 要求请求的时间**恰好等于**该确认分钟，才调用 RPC 写库。RPC 还带 `p_baseline_time` 并发保护（当前 active 时间必须仍是会话开始时的基线）。

### 7.3 验证

- `npx tsx --test tests/*.test.ts`：**1076 全通过**（含 12 个新测试）。
- `npx tsc --noEmit`：新文件零错误（仓库剩余 5 个为预先存在）。
- `npx eslint`：新文件零错误零警告。

### 7.4 待办/注意

- **引擎端点鉴权**：`rectification-save-birth-time` 走的 RPC 仅 service_role；引擎各 rectification 端点无需 token（与 `runConsultationWorkflow` 一致）。
- **计费**：按消息 reserve/complete/cancel 咨询点数（复用 `begin/complete/cancel_consultation_credit`）。
- **v4 保留**：有进行中 v4 case 时仍走 v4 面板恢复，不丢数据。
- **模型**：默认走当前模型目录；若想让叙事用 Claude，在 `LLM_MODELS_JSON` 加 Claude 项并把 `LLM_DEFAULT_MODEL_ID` 指过去即可。
- **部署**：新路由无需新环境变量（复用 `JYOTISH_API_BASE`、Supabase 密钥、模型目录）；新迁移需在 staging 执行 `db:migrate`。
