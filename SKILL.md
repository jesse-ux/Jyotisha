---
name: jyotish-vedic-astrology
version: 6.9.14
description: 印度占星（Jyotish）专业解盘与推运系统。核心能力：PDF星盘输入→严谨解盘→精确推运应期输出。35种Dasha、405+Yoga规则、KP系统、Prashna卜卦、16因子合盘、Remedies补救、Sahams部分覆盖、Sudarshana三参考点、PMC完整检测、Tajika年度星盘、案例验证+误区纠正。触发词：印度占星、吠陀占星、Jyotish、解盘、推运、星盘分析、Dasha、Transit、Nakshatra、Yoga。GitHub: https://github.com/732642856/yinduzhanxing
---

# 印度占星专业解盘与推运系统

> **版本**：v6.9.14 | **详细变更**：`CHANGELOG.md`
> **对标状态**：中文用户端与技法覆盖领先；D1/D9/AV/Chara 等有守门，Dasha/Shadbala 外部 oracle 扩充仍在进行。
>
> **真相边界**：当前问题已不是“完全缺技法名称”，而是少数高价值传统深度仍未闭环；请优先修复精度与裁决链，而不是继续表面堆功能名。
> **执行总控**：`references/quick-reference-guide.md`
> **严格路由**：`references/strict-workflow-router.md`（涉及事业/婚恋/财务/应期/技法验证时必须优先读取）
> **机器注册表**：`references/technique_registry.json` + `scripts/audit_capabilities.py`
> **文章级细节模板**：`references/interpretation_template_registry.json` + `scripts/validate_interpretation_templates.py`

## v6.9.14 核心能力

| 维度 | 数据 |
|------|:--:|
| Dasha系统 | 35种（含Vimshottari/Chara/Kalachakra/Narayana/Yogini等；成熟度不完全一致，以 registry 边界说明为准） |
| Yoga规则 | 405+条（BPHS数据驱动架构，Yoga精度Benchmark 100%） |
| 分盘 | D1-D144 + D2/D3变体 + 复合D-m×n + 自定义D-N(2-300) |
| Bhava Chalit | Sripati/Porphyry/Equal/Whole Sign/Placidus/Koch 不等宫位调整 |
| Sudarshana | Asc/Moon/Sun 三参考点盘 + 宫位收敛分析 |
| Shadbala | absolute Rupa 分量求和；内部不变量通过，外部绝对值 oracle 扩充中 |
| Ashtakavarga | BAV+SAV+PAV（展开式）+Sodhita（净化式） |
| KP系统 | Sublord+Subsublord+ABCD Significator（输出可用，细粒度传统口径仍以实测与案例闭环为准） |
| 合盘 | 16因子36分制（Ashtakoot+Kuta） |
| 补救 | 5类（宝石/咒语/捐赠/斋戒/Dosha专项） |
| 自动化测试 | pytest/quality gate 分层守门；以当前仓库质量门输出为准 |
| Git commits | v6.1.12→v6.9.14 持续推进 |

**独有能力**：中文AI解读引擎、Career/Love结构化分析、验前事反推管道、误区自动纠正、名人+普通人案例双轨验证。

## Yoga 逻辑验证指标

| 指标 | v6.0.45（旧基线） | v6.9.14（当前） |
|---|---:|---:|
| Precision | 83.26% | **96.48%** |
| Recall | 91.52% | **93.99%** |
| **F1 Score** | 87.19% | **95.22%** |
| 规则库 | 82条 | **405条** |
| Yoga精度Benchmark | — | **100%** (8/8) |

---

## ⚠️ 核心定位

**三种输入 → 严谨解盘 → 精确推运应期输出**

| 路径 | 用户输入 | AI行为 |
|------|---------|--------|
| **A：精准出生信息** | 日期+时间+地点 | `full-reading` 引擎全链路计算 |
| **B：PDF/文字星盘** | PDF/详细文字描述 | 提取数据+Quality Gate → `references/pdf-chart-reading-guide.md` |
| **C：时间不明确** | "不知道几点出生" | 互动式出生时间矫正 → 确认后走路径A |

### 用户不会提问时的默认行为

用户只给出生信息、没有具体问题时，不要反问“你想看什么”，也不要只输出模板解读。
默认先运行统一主链生成 `evidence_packet`、`guided_topics` 与 `Technique Audit Table`，再把 `guided_topics`
按优先级展示为可直接选择的问题。

执行顺序：

1. MCP/Skill 环境优先调用 `strict_workflow` 或统一 consultation workflow。
2. `question` 可先填：`请先生成 guided_topics 并推荐我最值得看的问题`。
3. 输出 3-5 个系统建议主题，每个主题必须带：数据依据、置信度、blocked/partial 项、可直接继续问的问题。
4. 用户选择主题后，再按 career / relationship / wealth / health / timing strict workflow 进入专题。
5. VedAstro 没有 `raw_response` 时，只能标 `official_blocked` 或 `local_fallback`，不得声称云端闭环。

普通用户 / AI 应用调用前，先运行：

```bash
python3 scripts/user_invocation_acceptance_check.py
```

该命令必须返回 `"status": "pass"`，并显式列出 VedAstro / PyJHora-JHora / jyotishganit 的可用、partial 或 blocked 状态；否则不得声称云端 Git 仓库调用已可高质量使用。

### 首次调用与降级合同

普通用户不必先理解 API、MCP、分盘或校时方法。Skill/MCP 首次调用必须先使用
`skill_onboarding`：缺出生字段时只收集日期、时间、经纬度；出生时间有误差时返回
`rectification` 的选择题问卷；时间明确时进入 `direct_chart`。不得要求用户先提交长篇
人生事件表。

安装或运行异常时调用 `skill_doctor`。它只报告本地资产与外部适配器 readiness，不得把
adapter available 解释为已完成 VedAstro、PyJHora/JHora 或 jyotishganit raw-oracle 校验。

每个工作流结果必须包含 `execution_status`：

- `official_verified`：仅此状态可说 VedAstro 官方 raw evidence 已被使用；
- `official_blocked`：官方请求失败、额度/网络/超时受阻；
- `local_fallback`：本地计算继续可用，但不能称为官方云端闭环。

### Web/API 任务存储

默认 `JYOTISH_ASYNC_JOB_BACKEND=file` 使用本机受限权限的临时任务文件。单机部署可设
`JYOTISH_ASYNC_JOB_BACKEND=sqlite`，使用 `scratch/local/async_jobs.sqlite3` 保存 token-hash
与 TTL 任务记录。两种后端都不是 Redis、多节点队列或跨主机 worker；不得把它们描述为分布式恢复能力。

**强制工作流**（完整规范 → `references/ai-reading-workflow-prompt.md` v5.1.0）：

0. **阶段负一**：问题类型路由（事业/婚恋/财务/应期/历史验证/综合解盘）→ 必须先读 `references/strict-workflow-router.md`，按对应 strict checklist 执行；用户不需要主动点名高级技法。
0.1 **事件判定骨架**：凡涉及 marriage / career / wealth / event verify，必须执行 `事件判定骨架 v1.0`，按 `Route -> Evidence Ledger -> Adjudication -> Output Contract` 顺序输出；不得再凭直觉跳模块或随口给置信度。详见 `references/ai-reading-workflow-prompt.md`、`references/event_judgment_skeleton.md`、`references/event_judgment_marriage.md` 与 `references/event_judgment_examples.md`。
1. **阶段零**：入口路由（A/B/C自动判断）
2. **阶段一**（仅B）：PDF/图片提取 + Quality Gate
3. **阶段二**：意图识别 → 路由目标宫位（无明确意图→Level 2综合解盘）
4. **阶段二点五**：若 `full-reading` 或网页/API 返回 `ai_prompt_pack`，必须优先读取 `prompt_zh`、`evidence_snapshot`、`retrieval_plan` 作为 AI/RAG 主上下文；若没有该字段，再退回传统 JSON 摘要。
4.1 **VedAstro 官方优先级**：用户给出生信息后，网页、Skill、MCP 都必须默认走同一条数据优先级：`VedAstro official snapshot -> local supplemental modules -> local fallback only when official blocked`。用户不需要主动要求“调用 VedAstro”。若 `evidence_snapshot.vedastro_official_full_snapshot.status` 为 `ok/partial` 且官方 chart 可用，D1/分盘/官方返回的原始字段以 VedAstro 为主；本地引擎只做补充、交叉检查或官方 blocked 时 fallback。
4. **阶段三**：静态分析10步（宫位→承诺→Yoga→Argala→逆行→NK→Shadbala→AV→Ketu→分盘）
5. **阶段四**：动态推运7步（Dasha→五系统Convergence→Transit→Double Transit→Jaimini→KP→Varshaphala）
6. **阶段五**：应期输出（五层验证→时间窗口→Actionable Output+案例检索）
7. **阶段六**：补救措施（可选）
8. **阶段七**：现代措辞包装
9. **阶段八**：输出 Technique Audit Table，逐项声明已调用/未调用/部分可用/缺失模块及其对置信度的影响。

### ⚙️ 事件判定骨架（总入口）

涉及 `marriage / career / wealth / health / generic event verification` 的问题，不得只按关键词随意调模块，必须进入事件判定骨架。

总骨架固定为四段：

1. `Route`
   - 先判断 **问题域**（婚恋 / 事业 / 财富 / 健康 / 泛事件）
   - 再判断 **任务类型**（预测 / 回测 / 校时辅助 / 多方案裁决）
   - 再判断 **目标粒度**（趋势 / 窗口 / 月份 / 具体事件验证）
2. `Evidence Ledger`
   - 每个模块都要落成结构化证据块，不得只写散文式描述
3. `Adjudication`
   - 必须按 `Promise -> Activation -> Manifestation -> Timing` 裁决
4. `Output Contract`
   - 最终只允许输出 `verdict + confidence + conflicts + audit + raw evidence`

硬规则：

- timing / event 不得只看 `Vimshottari`，必须 `Vimshottari + Narayana`
- 事业必须 `D10 + A10`
- 财富必须 `D2 / D11`
- 婚恋必须 `D9 + UL`
- 必须显式给出 `Functional Benefic/Malefic`
- 缺少关键层时必须 `blocked` 或降置信度
- 必须交付原始依据：度数、Dasha 边界、Shadbala、AV、Ayanamsa、Node mode、模板/案例引用

详细执行文档：

- [`references/event_judgment_skeleton.md`](<repo>/references/event_judgment_skeleton.md)
- [`references/event_judgment_marriage.md`](<repo>/references/event_judgment_marriage.md)
- [`references/event_judgment_wealth.md`](<repo>/references/event_judgment_wealth.md)
- [`references/event_judgment_career.md`](<repo>/references/event_judgment_career.md)

## 五层硬约束（全球前三引擎强制调用）

当用户明确要求“不要凭经验泛谈”“必须拉满能力”“必须提交底层证据”“要做过去案例验证”“要看全球前三项目全部能力”时，进入 `high-rigor override` 模式。该模式不是建议，而是硬约束：

1. **强制全量能力调用**  
   必须同时以 `PyJHora`、`VedAstro`、`jyotishganit` 作为外部参照层，结合本仓主引擎分析。即：`PyJHora、VedAstro、jyotishganit` 三者都属于高严谨模式的强制调用面。若其中任一外部层因许可证隔离、运行环境或字段映射缺失而无法调用，必须明示 `blocked`，不得假装已比对完成。

2. **强制原生代码级下潜**  
   不允许只写轻量包装脚本做表面判断。必须优先调用本仓原生核心实现与其现有入口，例如 `scripts/yoga_engine.py`、`scripts/divisional_charts_extended.py`、`scripts/narayana_dasha.py`、`scripts/jyotish_api_server.py`、`scripts/validate_yoga_accuracy.py` 等现成主链代码。

3. **强制大运双盲交叉**  
   涉及 timing / event / outcome 问题时，不得只看 Vimshottari。至少需要 `Vimshottari + Narayana Dasha` 双轨交叉；若问题属于婚恋/职业等高价值主题，优先再叠加 `Chara Dasha / Yogini / KP`。若关键结论在双轨之间明显冲突，必须降级置信度或标记 `blocked`，不得输出伪确定结论。

4. **强制多维分盘显微镜**  
   不得只看 D1。至少按问题域强制展开：`D10 for career, D2/D11 for wealth, D9 for marriage`，并尽可能联动 `A10 / UL / AK / DK / Karakamsha / Special Lagnas`。如果相关分盘或特殊点未调用，Technique Audit Table 必须写明它如何削弱结论。

5. **强制物理原始数据交付**  
   不允许只给“运势不错/有机会”式结论。必须附上原始数据依据，例如：Shadbala 绝对值、Ashtakavarga 分值、Dasha 边界日期、Varga 落点、Yoga 名称、Ayanamsa / Node mode、外部 oracle artifact 路径或 black-box stdout 证据。原始数据交付是高严谨结论的唯一有效依据。

诚实边界：

- 若 `PyJHora / VedAstro / jyotishganit` 中任何一层无法合法或稳定调用，必须明确说明缺口来源。
- 若外部 oracle 尚未闭环，不得把内部一致性伪装成“全球第一级精度”。
- 若用户问题只给出模糊数据，必须先降低结论等级，而不是脑补。

---

## ⚠️ 强制规则（与"不跳步"同级）


### 用户隐私与个案资料隔离（v6.0.4-privacy）

**严禁把真实用户个人信息写入 skill 文件或公开仓库。**

包括但不限于：姓名/称呼、出生日期时间地点、星盘度数、人生事件、关系状态、职业经历、项目背景、历史回测结论、当前会话中的个案分析。

允许的资料来源只有三类：
1. 公开 AA 级名人案例；
2. 明确标注为虚构的 smoke test / template；
3. 用户在当前会话中主动提供的数据，但只能在当前会话中使用，不得持久化到 skill、tests、CHANGELOG 或公开仓库。

如需沉淀方法论，只能抽象为通用规则，不得保留可识别个人轨迹的细节。

### Strict Workflow Router（v6.0.1-orchestration）

**凡是用户询问事业、婚恋、财务、事件应期、历史回测或技法可靠性，必须先读取 `references/strict-workflow-router.md`。**

核心要求：
1. 先判断问题类型，再自动选择 `career-timing-strict` / `relationship-timing-strict` / `wealth-timing-strict` / `event-timing-strict` / `event-verification-strict`。
2. 用户不需要知道 Chara Dasha、A10、Argala、Shadbala、Ashtakavarga 等技法名称；AI 必须按问题类型自动调用。
3. 输出末尾必须给出 Technique Audit Table，说明每项高级技法是否调用、结果是什么、缺失会如何降低置信度。
4. 不得把未实现或未调用的技法静默省略；A10/Karma Pada、Pushkara、Vargottama、Dasha Sandhi 已进入 full-reading 输出；Bhava Chalit 与 Sudarshana Chakra 已进入 complete，可正常纳入 Technique Audit Table。

### MEVG 强制外部验证门控（v4.2.0+）

**所有解读结论必须经过外部权威来源验证，禁止仅凭 AI 训练记忆输出。**

| 门控 | 位置 | 职责 |
|------|------|------|
| Step 3.11 | 静态分析后 | 验证 Yoga/尊严/Shadbala/SAV |
| Step 4.10 | 动态推运后 | 验证 Transit/Dasha/天文现象 |
| Step 5.5 | 预测输出前 | 确认每条预测有来源+置信度一致 |

**三步验证法**：V1 构建英文查询词 → V2 web_search ≥3个独立来源 → V3 交叉验证仲裁分歧

→ 完整协议：`references/mandatory-verification-gate-protocol.md`

### Transit Actionable Output（v4.1.0+）

**每条 Transit 预测必须输出三要素**：
1. **时间段**（精确到日/周/月）
2. **具体行动类型**（做什么）
3. **置信度** [A]=已验证 / [B]=高概率(3+维度) / [C]=推断(单一维度)

→ 完整规范：`references/transit-actionable-output-guide.md`

### Rahu/Ketu 节点口径冻结（v6.0.7-node-mode）

**所有 benchmark 与解盘输出必须显式声明 Rahu/Ketu 使用 Mean Node 还是 True Node。**

- 当前 skill 默认：`--node-mode mean`（Swiss Ephemeris Mean Node）。
- 可选：`--node-mode true`（Swiss Ephemeris True Node，用于对齐 PyJHora 默认口径）。
- PyJHora 4.8.6 的 `rasi_chart()` 默认使用 True Node；第三轮 benchmark 的 Rahu/Ketu 差异已由第四轮仲裁确认为 Mean/True Node 口径差异，不应再误判为 D9/D10 计算 bug。
- 输出 `birth_info.node_mode` 与 `node_mode_note` 必须保留，作为参数冻结证据。

### Multi-Ayanamsa 与 Prompt Pack 冻结（v6.9.15-ai-native）

**所有排盘、网页/app 和 AI 解读必须显式携带 Ayanamsa 与 Prompt Pack 证据。**

- `full-reading --ayanamsa lahiri|raman|kp` 与 `/api/chart` 的 `ayanamsa` payload 会影响黄经计算；不得在用户选择 Raman/KP 时仍假定 Lahiri。
- 输出优先读取 `birth_info.ayanamsa_name`、`birth_info.ayanamsa_display`、`birth_info.ayanamsa`；网页/app 的 `birth.ayanamsa_display` 同样视为参数真源。
- AI 解读必须优先消费 `ai_prompt_pack.prompt_zh`、`ai_prompt_pack.evidence_snapshot`、`ai_prompt_pack.retrieval_plan`，并在结论中保留“不要仅凭单一配置下结论”的证据交叉要求。
- 若浏览器 fallback 无法实时切换 Raman/KP，应明确提示需启动本地 API 服务；不得把 fallback 结果伪装成已按目标 Ayanamsa 重算。

### Dasha/Shadbala 外部校准边界（v6.9.15-oracle-evidence）

**普通用户解释时必须显式区分基础排盘高可信与高阶绝对值待外部校准。**

- Dasha-only 外部证据当前目标集已闭环：`dasha_external_oracle_evidence_validation.valid_dasha_packets: 3/3`；Steve Jobs / Lahiri、synthetic Lahiri template 与 1800 Delhi historical epoch 的 Vimshottari 起始边界来自 PyJHora 4.8.7 隔离黑盒 stdout artifact。
- 全局 Dasha/Shadbala Calibration Status 仍未完成：`external_oracle_evidence_validation.valid_packets: 4`，`ready_for_calibration: 4`；Shadbala 外部绝对值当前目标集已通过 4/4，Raman 扩展样本与非 Dasha 靶点尚未封顶。
- 历史 UI 静态门禁仍保留旧提示 `ready_for_calibration: 0` 作为“不得过度宣称”的保守文案；实际进度必须以当前 `oracle_collection_queue.py` / `oracle_evidence_validator.py` 输出为准。
- Tajika/Sahams 年运外部样本已开始闭环：`tajika_sahams_annual_benchmark_dashboard.ready_for_calibration: 1/5`；Steve Jobs 1984 Varshaphala/Lahiri 的 solar return、Varsha Lagna、Muntha、Year Lord、Mudda Dasha 首主、三项 Sahams 与 Tajika Yogas 已由 PyJHora 4.8.7 隔离黑盒 artifact 验证，下一优先级为 Einstein 1905。仍不得声称 Tajika/Sahams 年运体系已全局封顶。
- D1/D9/SAV 高可信；Dasha 精细日期可引用已验证 Dasha-only 样本的局部进度，但不得把全部大运边界、Shadbala 绝对值或全局精度说成已完成外部校准。
- 不得把大运起点或 Shadbala 绝对值说成已完成外部校准；涉及具体日期/绝对力量值时，必须同时报告 `Dasha/Shadbala Calibration Status`、`external_oracle_evidence_validation` 与 `production_tuning_allowed: false` 边界。
- `production_tuning_allowed: false` 前，禁止为了贴合单份 PDF、单个 JHora 截图或本仓库本地输出而改生产常数。
- 对普通用户的建议话术：基础落座、D9、SAV 可作为稳定证据；当前 Dasha-only 目标集已完成外部黑盒验证，但多 Dasha 家族、Antardasha/Pratyantar 细边界仍需扩展；Shadbala 当前目标集已有四个外部六分量样本，绝对值断语可引用 4/4 闭合进度；但跨软件差异、Raman 扩展样本与公开书例仍需更多证据后再提升到全局置信。
- 工作流要求：Dasha-only packet 用 `python3 scripts/dasha_oracle_evidence_validator.py --queue-file <queue.json>` 验证；全局校准仍必须跑 `python3 scripts/oracle_evidence_validator.py --queue-file <queue.json>`，两者不可混用。

### Ashtakavarga 口径冻结（v6.0.8-av-calibration）

**Ashtakavarga 默认使用 BPHS/PVR 书例校准口径，必须保留 SAV=337 与 full SAV=386 不变量。**

- `scripts/ashtakavarga.py` 当前为 v2.1：经第六轮 PyJHora/PVR 公开书例仲裁，校准 Moon/Venus 的 7 个贡献表项。
- 输出 `method` 应显示 `Ashtakavarga八分法（BPHS/PVR书例校准v2.1）`。
- benchmark 若与其他软件不一致，先比较贡献表项和 SAV 总量，不得直接把口径差异判为运行 bug。

### Chara Dasha 能力升级（v6.1.12 benchmark验证通过）

**Chara Dasha KN Rao Method 正式 benchmark 通过（95.83% ≥ 95%），可作为标准应期模块使用。**

- v6.1.12: PyJHora oracle benchmark **10案例×12星座=120对**: Sign 100%, Dur 91.67%, Overall 95.83% ✅ PASS
- v6.1.11: 重写为完整 KN Rao Method（序列基于第9宫方向，时长基于宫主所在宫位+尊贵调整）
- 剩余~4.2%差异: Aquarius/Scorpio 的 Rahu/Ketu 共主动态判定（需复制 PyJHora _stronger_planet_new）
- `jaimini` 输出中的 Chara Karaka、AK/AmK、Karakamsha 继续可用。

### 开源复用边界冻结（v6.9.16-reuse-whitelist）

**后续 skill 深化优先复用 MIT 资产，禁止继续对 AGPL/闭源项目做“看着像就手写一份”的低效重复工作。**

- 可直接复用主来源：
  - `jyotishganit`（MIT）：Shadbala / Bhava Bala / Panchanga / Vimshottari 常数与实现思路
  - `VedicAstro`（MIT）：KP / Horary / API workflow
  - `jaimini-tropical`（MIT）：Jaimini / Arudha / Chara Dasha 方向常数与细分规则
  - `dashaflow`（MIT）：合盘 / Muhurta / 部分 Jaimini / dignity / Yoga 规则
- 仅允许黑盒对标、禁止复制实现：
  - `PyJHora`（AGPL）
  - JHora（闭源）
  - `hora-prakash`（AGPL）
- 本仓已落地的 MIT 复用点包括：`kp_system.py`、`synastry.py`、`muhurtha_election.py`、`bhava_bala.py`、`dasha_calculator_enhanced.py`、`jaimini.py`、`constants/mit_imported_constants.py`
- 继续扩 skill 前，先查 `<repo>/docs/research/reuse_license_whitelist_for_skill_2026_06_26.md`，避免重复造轮子或踩许可证边界。

### Transit 真实过境冻结（v6.0.10-true-transit）

**full-reading 中的 Transit 多参考点分析必须使用真实过境行星位置，不得复用本命行星位置。**

- `modules.transit_positions` 必须输出 `data_layer: true_transit_positions`、`target_date`、`node_mode` 和 Swiss Ephemeris 计算的过境行星位置。
- `modules.transit_multi_reference` 必须读取 `transit_positions.planets`，并输出同样的 `data_layer: true_transit_positions`。
- `--transit-date YYYY-MM-DD` 可显式指定过境日期；若未提供，则跟随 `--today`，再否则使用当前日期。
- 第八轮 benchmark 已用 10 个公开/虚构 smoke case 对齐 Swiss Ephemeris：340/340 字段匹配，0 mismatch。

### Shadbala 能力边界（v6.9.14-shadbala）

**当前 Shadbala 在注册表中为 covered，主输出为 absolute Rupa 分量求和，可作为内部一致的相对强弱参考；首个外部绝对值六分量样本已通过，但不得声称全部 Shadbala 绝对值已完成校准。**

- 当前 benchmark 验证 `shadbala` 子命令与 `full-reading.modules.shadbala` 的六重分量求和、Virupa/Rupa 换算和 total invariant；用户样本已输出 absolute Rupa。
- v6.9.12 已升级 Nathonnata Bala 连续化与 Drik Bala Sputa Drishti 精确相位，v6.9.14 注册表状态为 `covered`。
- 通过项包括：结构完整性、六重力量组件范围、总分聚合、Virupa/Rupa 换算、排名、full-reading 一致性。
- 仍需保留边界：部分 Saptavargaja 子分盘与 Chesta Bala 速度分档仍需更多外部绝对值对标。
- 因此 `technique_registry.json` 中 Shadbala 状态为 `covered`，但涉及精确力量断语时必须加置信度上限，直到更多 JHora/公开书例等完整外部绝对值对标通过。

---

## 核心能力速查

> 详细说明和参考文件索引 → `references/quick-reference-guide.md`

| 能力域 | 核心内容 | 主要参考文件 |
|--------|---------|------------|
| **静态分析** | 行星配置、Yoga、NK、宫位、Argala、Shadbala、AV、Badhaka、Raman方法论 | `planets.md` `yoga_list.md` `argala-complete-guide.md` `badhaka-obstacle-planet-guide.md` `raman-house-judgment-methodology.md` |
| **动态推运** | Vimshottari、Chara Dasha（KN Rao Method, covered）、KP、Double Transit、Varshaphala、替代Dasha | `vimshottari_dasha_guide.md` `dasa-convergence-methodology.md` `alternative-dasha-systems.md` |
| **Jaimini静态层** | Chara Karaka、Karakamsha、A1-A12/UL、Graha Pada、Argala/Virodhargala、Special Lagnas（部分） | `jaimini-complete-system.md` `argala-complete-guide.md` `technique-capability-matrix.md` |
| **关系占星** | Koota 36分、Mahendra/Stree Deergha/Vedha/Rajju、D9伴侣、DK、Mangal Dosha、Papasamya、配偶六层确认 | `spouse-multi-layer-methodology.md` `darakaraka-complete-guide.md` `relationship-astrology-guide.md` |
| **出生时间矫正** | 八大方法、自动化流程、验证报告、分盘调用决策树 | `birth-time-rectification-advanced.md` `birth-time-rectification-decision-tree.md` |
| **PDF读取** | JH/PL PDF全量提取、完整性门、交叉校验 | `pdf-chart-reading-guide.md` `data-bridge-mapping.md` |
| **Prashna问事** | 十步断卦、AL、Sphuta、Sahams、失物查询 | `prashna-complete-guide.md` `single-event-inquiry-protocol.md` |
| **多元技法** | Yogi/Ava Yogi、Tithi Lord、Rashi Tulya Navamsa、BCP、Bhrigu Pada、Pancha Pakshi、Tara Bala、Deha/Jeeva、Moolatrikona、Shodasavarga/Vimsopaka、Ashwini/Abhijit/Ketu星宿专题（需保留成熟度边界） | `yogi-avayogi-system.md` `yogi-asc-tight-orb-wealth-freeze-guide.md` `tithi-lord-relationship-system.md` `tithi-lord-freeze-execution-guide.md` `rtn-high-order-d9-freeze-execution-guide.md` `bhrigu-pada-all-event-freeze-execution-guide.md` `ashwini-abhijit-ketu-nakshatra-freeze-guide.md` `bhrigu-chakra-paddhati.md` `shodasavarga-complete-guide.md` `planetary-dignity-complete-reference.md` `alternative-dasha-systems.md` |
| **精准方法论** | PACDARES框架、九层复合方法、L3矛盾检查、三级置信度 | `precision-reading-methodology.md` |
| **解读质检** | 真实解读结构质检、参数冻结、分盘强制展开、oracle 诚信边界 | `real-reading-quality-checklist.md` |
| **现代解读** | 现代措辞映射、现代生活场景、常见误判纠错 | `modern-language-guide.md` `common-misconceptions.md` |
| **实战智慧** | ⭐反教条主义经验精华（全球占星师真实案例反馈总结） | `practitioner-wisdom-anti-dogma.md` |
| **验证与错题** | 深度数据审计、技法缺陷与修复、推运反思、15+名人验证案例 | `audit-*` `lessons-learned-*` `verified-celebrity-cases-*` |

## 文章级细节模板入口（v6.9.17-template-registry）

用户问到“吉祥天女/财富点、Yogi Point、娄宿 Ashwini 天赋、上升点度数定位、紧密合相、RTN/D9、Bhrigu Pada、Tithi Lord、Pancha Pakshi/Swara”等细颗粒技法时，不得临场凭记忆发挥，也不得把网上文章断语直接当权威。

必须先查：

```bash
python3 scripts/validate_interpretation_templates.py --format markdown
```

注册表真源：

`references/interpretation_template_registry.json`

当前已冻结 6 个可复用模板：

1. `yogi_asc_tight_orb_wealth`：Yogi Point / 上升度数 / `<1°` 紧密合相 / 财富激活
2. `ashwini_talent_profile`：Ashwini / Ketu 系星宿 / Abhijit 择时边界
3. `rtn_high_order_d9`：Rashi Tulya Navamsa / 高阶 D9 异象
4. `bhrigu_pada_all_event`：Bhrigu Pada / Arudha Pada 全事件推进
5. `tithi_lord_relationship`：Tithi Lord 关系与情绪节奏
6. `pancha_pakshi_swara_boundary`：Pancha Pakshi / Swara 择时边界

使用规则：

- 这些模板是“细节解释层”，不能替代 D1/D9/Dasha/Transit/相关分盘。
- `<1°` 紧密合相只能提高敏感度或置信度，不能单独断财富、婚姻、事故或成就。
- Ashwini/Abhijit/Ketu 星宿只能作为天赋、行动风格或择时偏好，不可单独断职业、财富或灵性高低。
- Bhrigu Pada / RTN / Tithi Lord / Pancha Pakshi 必须作为辅助确认层；若没有主承诺和推运激活，输出置信度不得超过 C。
- 所有文章/课程/网上说法默认归入 B/C 级线索，必须经过注册表中的 `required_cross_checks` 与 `forbidden_claims` 过滤。

## 当前最硬的未闭环点

> 这部分比“再加几个技法名”更重要，决定 skill 距离传统软件级深度还有多远。

1. **Dasha 外部绝对边界闭环**
   - 当前 `ready_for_calibration: 4`
   - Dasha-only 目标集已由 PyJHora 黑盒证据推进到 3/3，但全局 Dasha/Shadbala 队列仍有非 Dasha 靶点缺字段，`production_tuning_allowed: false`
2. **Shadbala 外部绝对值闭环**
   - 当前 absolute Rupa 结构自洽，但还不是外部绝对值完全校准
3. **Chara Dasha 共主仲裁尾差**
   - KN Rao benchmark 已过，但 Aquarius/Scorpio 的 Rahu/Ketu 共主强弱仲裁仍有尾差
4. **KP ruling planets / 事件裁决细节**
   - KP 表层输出可用，但传统工作流深度仍需继续闭环
5. **Prashna 分支工作流**
   - 问事类型分支、裁决链、时机判断仍需更稳定的传统链路
6. **Varshaphala / Tajika / Sahams 年运裁决深度**
   - 年盘骨架已在，第一条 Steve Jobs 1984 外部年运样本已闭环；但整体仍只有 `1/5`，事件裁决、权重层、Einstein 1905 等后续样本仍需继续成熟
7. **Kalachakra / Narayana 等替代 Dasha 的成熟度边界**
   - 已有覆盖，但部分子层、边界口径、外部黑盒对照仍需继续收紧
8. **高阶解释层整合**
   - `Pushkara / Vargottama / Avastha / RTN / Inter-chart linkage` 已存在，但还未形成传统高手式稳定裁决层

完整排序见 `<repo>/docs/research/current_skill_core_gap_rerank_2026_06_26.md`。

### Skill Gap Truth Audit（严禁过度声明）

当用户问“是否已经全球第一”“是否包含所有印度占星技法”“过去案例哪里错了”“还差什么硬任务”时，必须先运行：

```bash
python3 scripts/skill_gap_truth_audit.py --format markdown
```

真源文件：

`references/skill_gap_truth_registry.json`

此审计的结论优先级高于口头记忆：

- 若 `can_claim_global_first: false`，不得宣称全球无争议第一。
- 若 `can_claim_all_skills_complete: false`，不得宣称所有技法已完全封顶。
- 若 `can_claim_perfect_accuracy: false`，不得宣称排盘、Dasha、Shadbala、年运等已达到完美精度。
- 若某技法为 `covered`，只能说“有稳定入口或可用层”，不能自动说成 `complete`。
- 过去案例分析若触及 `past_case_analysis_corrections` 中的误判类型，必须主动修正并降低置信度。

## 全球开源定位

**当前还不能诚实地说这是全球开源印度占星 / 吠陀占星项目里的无争议第一。**

更准确的判断是：

- 在**中文 skill 工作流、本地可用性、产品化组织、MIT 资产整合**上，已经处于第一梯队。
- 在**长期黑盒 benchmark、传统软件级精度闭环、全球社区势能**上，仍落后于部分头部项目。

### 主要对标对象

1. **PyJHora**
   - 优势：47 Dasha、300+ 分盘、284+ Yoga、6800+ 级别验证与 JHora 对照壁垒
   - 边界：AGPL，只能黑盒 benchmark，不可复制实现
2. **VedAstro**
   - 优势：全球社区势能更强，API/Web/AI 平台生态更成熟
   - 边界：更偏平台化，全局离线本地 skill 体验不一定更优
3. **VedicAstro / jyotishganit / jaimini-tropical / dashaflow**
   - 价值：MIT，可直接作为继续补深的合法资产来源

完整定位分析见 `<repo>/docs/research/global_open_source_positioning_of_skill_2026_06_26.md`。

## 冲顶路线

> 如果目标是冲击“全球开源第一梯队”，后续优先级必须按这个顺序推进。

### P0 - 精度护城河（不完成就不能宣称“精准度完美”）

1. 冻结 `Dasha` 外部 oracle
2. 冻结 `Shadbala` 外部绝对值 oracle
3. 建立可重复、可公开的 benchmark 报表与案例链

### P1 - 传统裁决深度（不是补技法名，而是补传统工作流）

4. 收紧 `Chara Dasha` 共主仲裁尾差
5. 补深 `KP ruling planets / Horary workflow`
6. 补深 `Prashna` 问事分支裁决链
7. 补深 `Varshaphala / Tajika / Sahams` 的年度解释层
8. 收紧 `Kalachakra / Narayana` 的成熟度边界与黑盒一致性说明

### P2 - 老练度与口感（决定“像不像老练传统占星师”）

9. 继续补 `Pancha Pakshi` Tamil 细则
10. 整合 `Pushkara / Vargottama / Avastha / RTN / Inter-chart linkage` 的高阶解释层
11. 统一各输出面的边界表达，避免 `covered` 被误读成 `complete`

## 施工判断原则

> 后续所有优化都按这个判断，避免重复劳动或把“已覆盖但不够成熟”误判成“完全缺失”。

1. **先判断是不是已经存在**
   - 若 `scripts/`、`references/`、`skills/` 已有主体实现或执行链，优先视为“补成熟度/补入口”，不是重写。
2. **再判断是不是可合法复用**
   - MIT / Apache / BSD 资产优先复用；GPL / AGPL / 闭源只做黑盒对照，不复制实现。
3. **再判断是不是必须依赖外部 oracle**
   - 凡涉及 `Dasha` 精确日期边界、`Shadbala` 绝对值、传统软件口径冻结，必须走 JHora / PyJHora / 公开样本闭环。
4. **最后才决定是否新增技法**
   - 如果只是入口缺失、索引缺失、解释层不够厚，优先补入口和执行链，不先堆新名词。

---

## 计算引擎

**统一入口**：`scripts/jyotish_engine.py`（基于 Swiss Ephemeris）

```bash
PYTHON=python3
SCRIPT=~/.workbuddy/skills/jyotish-vedic-astrology/scripts/jyotish_engine.py
$PYTHON $SCRIPT <子命令> [参数]
```

### 37大子命令速查

| 子命令 | 功能 |
|--------|------|
| `full-reading` | ⭐全自动综合解盘（47模块一键出，含五系统Dasha收敛） |
| `chart` | 星盘计算+`--validate`附加R1-R10验证 |
| `dasha` | Vimshottari大运时间线+小运展开 |
| `yoga` | Yoga格局识别 |
| `predict` | 三层验证法事件预测+`--past-verify`验前事 |
| `varga` | 分盘计算（D9/D10等） |
| `varga-full` | BPHS十六分盘精确计算（D2-D60） |
| `celebrity` | 名人案例查询 |
| `db-stats` | 验证数据库统计 |
| `transit` | 行星过境查询 |
| `shadbala` | 六重力量计算（covered；absolute Rupa 输出，外部绝对值 oracle 完成前须保留置信度上限） |
| `ashtakavarga` | 八分法计算（SAV=337） |
| `memory` | Hermes记忆系统 |
| `validate` | R1-R10数学验证 |
| `audit` | P1-P12行星审计管线 |
| `aspects` | 度数精确相位系统 |
| `jaimini` | Jaimini Karaka/Karakamsha、A1-A12/UL、Graha Pada、Special Lagnas；Chara Dasha timing 为 KN Rao Method（covered；仍需保留共主仲裁与外部对标边界） |
| `nakshatra-adv` | 高级Nakshatra（Tara Bala+Chandra Bala+Sub-Lord） |
| `nakshatra-dasha` | 星宿大运推演（Ashtottari + Nakshatra-level Vimshottari） |
| `nakshatra-full` | 星宿综合报告（本命 + 大运 + 过境星宿） |
| `argala` | Argala门闩系统：主 Argala + Virodhargala + Rajayoga 分类 |
| `tajika` | Tajika年运盘（Muntha+YearLord+Mudda Dasha） |
| `synastry` | 合盘分析：Ashta Koota 36分 + Mahendra/Stree Deergha/Vedha/Rajju 等附加Kuta |
| `report` | MD→HTML报告生成（羊皮纸主题） |
| `prashna` | Prashna问事占星 |
| `double-transit-pac` | KN Rao Double Transit PAC+D9层 |
| `transit-ll7l` | Transit LL/7L连接+互换 |
| `planetary-congregation` | 行星聚集检测 |
| `vivah-saham` | Vivah Saham婚姻敏感点 |
| `audit-capabilities` | technique registry 校验 + route 审计表输出 |
| `kp` | KP完整分析（SubLord+SubSubLord+ABCD Significator） |
| `ashtakoot` | 36点合婚（8标准Kuta+7附加+Kuja Dosha） |
| `solar-return` | 太阳返照盘年运分析（Newton迭代精确返照） |
| `narayana-dasha` | Narayana Dasha星座大运 |
| `muhurta` | Muhurta择时分析 |

→ 完整参数和示例 → `references/quick-reference-guide.md`

---

## 核心方法论

### 三层验证法
1. **本命征象**：静态星盘中的征象
2. **大运激活**：Dasha系统激活相关宫位
3. **过境触发**：Transit系统触发具体事件（⚠️必须多参考点检查）

### 精准解盘方法论（v3.12.1）

**六大共识原则**：功能吉凶因盘而异 | 单一技法不做结论 | 规则前提先查 | 案例验证>经典引述 | 先整体后细节 | 先验证过去再预测未来

**PACDARES框架**：P位置→A相位→C合相→D财富Yoga→A灾厄Yoga→R皇家Yoga→E互换→S特殊

**九层复合方法**：L1 PACDARES → L2 分盘 → L3 矛盾检查(关键) → L4 Vimshottari → L5 AV+Transit → L6 条件Dasha → L7 Jaimini → L8 其他Jaimini → L9 Tajika

**三级置信度**：✅[A]已验证 / ⭐[B]强推断(3+维度) / ⚡[C]假设(单一维度)

→ 详见 `references/precision-reading-methodology.md`

---

## 强制规范速查

| 规范 | 版本 | 核心要求 | 参考文件 |
|------|------|---------|---------|
| MEVG外部验证 | v4.2.0 | 所有解读必须web_search验证 | `mandatory-verification-gate-protocol.md` |
| Transit Actionable | v4.1.0 | 预测必须输出时间段+行动+置信度 | `transit-actionable-output-guide.md` |
| 过境多参考点 | v1.9.0 | Lagna+Chandra Lagna双参考点(强制) | `transit-multi-reference-guide.md` |
| Ketu双属性 | v2.0.0 | 必须同时评估"放手"和"突破" | `ketu-dual-nature-guide.md` |
| Shadbala评估 | v6.9.15 | absolute Rupa 分量求和；外部绝对值 oracle 完成前须保留置信度上限 | `shadbala-complete-methodology.md` |
| Yoga Phala Timing | v2.1.0 | 识别Yoga后必须预测何时发生 | `yoga-phala-timing-guide.md` |
| 逆行/燃烧/战争 | v2.1.0 | 每颗行星检查三重叠加 | `retrograde-combustion-war-guide.md` |
| 精准方法论 | v3.12.1 | PACDARES+九层+L3矛盾检查 | `precision-reading-methodology.md` |

---

## 预测清单

- [ ] **Strict Router**：已读取 `references/strict-workflow-router.md`，并声明本轮使用的 strict route
- [ ] **Technique Audit Table**：输出末尾已列出已调用/未调用/complete/covered/仍需外部校准技法及置信度影响
- [ ] **MEVG-静态门控**：所有静态解读声明必须web_search验证
- [ ] 静态星盘分析（行星配置、Yoga、Nakshatra、宫位）
- [ ] Argala检查（2/4/5/8/11宫干预+Virodha）
- [ ] 逆行/燃烧/行星战争检查（三重叠加）
- [ ] Shadbala评估（absolute Rupa 分量求和；外部绝对值 oracle 完成前保留置信度上限）
- [ ] Ashtakavarga评估（BAV+SAV聚合校验337点）
- [ ] Ketu双重属性检查
- [ ] **MEVG-动态门控**：Transit/Dasha/天文现象必须验证
- [ ] Dasha推运（大运+小运+Pratyantar）
- [ ] Dasa Convergence五系统交叉验证
- [ ] Jaimini分析（Karaka/Karakamsha；Chara Dasha 已通过 KN Rao Method benchmark，剩余共主仲裁差异需声明）
- [ ] KP系统分析（Significator+Sub-Lord）
- [ ] Transit分析（多参考点强制）
- [ ] **Transit Actionable Output**（时间段+行动+置信度+案例检索）
- [ ] 分盘验证
- [ ] 预测边界检查（置信度标注，禁止绝对断言）
- [ ] **案例检索**：动态预测必须先检索真实案例
- [ ] **MEVG-预测门控**：确认每条预测有来源+置信度一致
- [ ] **缺口声明**：A10/Karma Pada、Pushkara、Vargottama、Dasha Sandhi 应从 full-reading 读取；若完整Bhava Chalit/传统Sudarshana等未计算，已说明原因与影响

---

## 参考资料索引

> 完整描述和版本信息 → `references/quick-reference-guide.md` §参考资料完整索引

共 **100+ 个文件**，按功能分组：

| 分组 | 数量 | 核心文件 |
|------|------|---------|
| AI工作流 | 2 | `ai-reading-workflow-prompt.md` ⭐ `quick-reference-guide.md` ⭐ |
| 核心方法论 | 9 | `common-misconceptions.md` `modern-language-guide.md` `pdf-chart-reading-guide.md` `prediction-boundary-protocol.md` |
| 基础知识 | 7 | `planets.md` `signs-and-houses.md` `nakshatra_deities.md` `vimshottari_dasha_guide.md` |
| Yoga体系 | 5 | `yoga_list.md` `neechabhanga-raja-yoga.md` `yoga-phala-timing-guide.md` |
| 宫位/场景 | 3 | `house-modern-mapping.md` `house-domain-planet-mapping.md` |
| 占星系统 | 5 | `jaimini-complete-system.md` `kp-astrology-complete-system.md` `remedies-complete-system.md` |
| 分盘/力量 | 7 | `ashtakavarga-complete-system.md` `shadbala-complete-methodology.md` `shodasavarga-complete-guide.md` |
| 过境/推运 | 9 | `transit-comprehensive-guide.md` `dasa-convergence-methodology.md` `alternative-dasha-systems.md` |
| 关系占星 | 5+ | `spouse-multi-layer-methodology.md` `darakaraka-complete-guide.md` `marc-boney-marriage-six-step.md` |
| 综合框架 | 5 | `comprehensive-reading-workflow.md` `deep-analysis-complete-workflow.md` |
| 高级技法 | 5 | `advanced-techniques.md` `global-astrologer-practical-methodology.md` |
| 案例库 | 13 | `famous-case-library.md` `verified-celebrity-cases.md` |
| 多元技法 | 5 | `yogi-avayogi-system.md` `bhrigu-chakra-paddhati.md` `pancha-pakshi-nakshatra-systems.md` |
| 高阶执行补充 | 8 | `deep-varga-avastha-execution-guide.md` `sahams-execution-guide.md` `high-order-d9-execution-guide.md` `tithi-lord-freeze-execution-guide.md` `rtn-high-order-d9-freeze-execution-guide.md` `bhrigu-pada-all-event-freeze-execution-guide.md` `yogi-asc-tight-orb-wealth-freeze-guide.md` `ashwini-abhijit-ketu-nakshatra-freeze-guide.md` |
| BPHS/Raman/Goel | 5 | `badhaka-obstacle-planet-guide.md` `raman-house-judgment-methodology.md` `vp-goel-jaimini-dasha-systems.md` |
| MEVG | 1 | `mandatory-verification-gate-protocol.md` |

---

## 注意事项

1. **出生时间精度**：±2分钟内最佳，可通过矫正提高
2. **三层验证法**：所有预测必须Dasha+Transit+Varga交叉验证
3. **现代场景优先**：所有解读使用现代措辞和现代生活场景映射
4. **解盘深度**：默认Level 2（专项），复杂问题自动升级Level 3
5. **不凭记忆**：禁止仅凭AI训练记忆输出解读结论，必须MEVG验证

---

**版本**：v6.9.15-calibration-boundary
**创建日期**：2026-04-20
**最后更新**：2026-06-26（skill 真源碎片已重新归拢并同步到 WorkBuddy；MIT 复用白名单已冻结；Chara/KP/Shadbala/Prashna/Tajika 的核心未闭环点已重排；外部 oracle 扩充仍在进行。）

---

## 验证与错题体系

> 基于万级案例库（15,807条AA级名人数据）和迭代验证沉淀的知识体系

### 数据资源

| 资源 | 规模 | 位置 |
|------|------|------|
| 名人案例库 | 15,807条（全部AA级） | `Claw/vedastro_data/PersonList-15k.csv` |
| 验证数据库 | 15,840 cases | `Claw/vedic_astrology_validation.db` |
| 验证结果JSON | v5/v6/v6.1 共325KB | `tests/test-data/` |

### 深度审计报告

| 文件 | 内容 |
|------|------|
| `audit-deep-data-audit-2026-05-04.md` | 逐字段对比pyswisseph，发现5个P0级Bug（Jaimini Karaka全错/Chara Dasha全0/Vimsopaka 16分盘全用D1/Yoga返回0/Arudha off-by-one） |
| `audit-skill-full-test-2026-05-04.md` | 27子命令逐项测试，full-reading 19模块全OK |
| `audit-kimi-optimization-review.md` | 外部AI优化建议审计，发现多处事实性错误 |
| `COVERAGE_AUDIT_REPORT.md` | 覆盖矩阵审计，综合覆盖率97.8%（90/92） |

### 经验教训（Lesssons Learned）

| 文件 | 核心教训 |
|------|---------|
| ⭐`practitioner-wisdom-anti-dogma.md` | **整合精华**：反教条主义十大死穴+技法盲区+全球占星师语录+验证规律（去重后统一入口） |
| `lessons-learned-misconceptions-reflection.md` | 解盘与推运常见误区（落陷≠失败/Rahu=非传统突破/12宫≠纯负面） |
| `lessons-learned-timing-reflection.md` | 推运应期判断的反思与修正经验 |
| `lessons-learned-technique-defects.md` | 技法缺陷全面分析 |
| `lessons-learned-technique-fixes.md` | 技法缺陷解决方案 |
| `lessons-learned-technique-patches-p1.md` | 技法漏洞修正方案 |
| `lessons-learned-technique-optimization.md` | 技法优化完整报告 |

### 已验证名人案例（平均吻合度93%）

| 文件 | 人物 | 吻合度 |
|------|------|--------|
| `verified-celebrity-cases-summary.md` | 10名人总览 | 平均93% |
| `verified-celebrity-cases-obama-web.md` | Obama | 95% |
| `verified-celebrity-cases-trump.md` | Trump | 94% |
| `verified-celebrity-cases-einstein.md` | Einstein | 92% |
| `verified-celebrity-cases-picasso.md` | Picasso | 93% |
| `verified-celebrity-cases-curie.md` | Curie | 94% |
| `verified-celebrity-cases-indira-gandhi.md` | Indira Gandhi | full-reading测试 |
| `verified-celebrity-cases-elvis.md` | Elvis | 93% |
| `verified-celebrity-cases-marilyn-monroe.md` | Monroe | - |
| `verified-celebrity-cases-michael-jackson.md` | M.Jackson | - |
| `verified-celebrity-cases-leonardo-dicaprio.md` | DiCaprio | - |
| `verified-case-reasoning-report.md` | 案例推理验证（修正版） | - |

### 星盘分析（7部分完整分析）

`analysis-natal-full-part1~7`：核心配置 / 宫位强度 / Ashtakavarga / PlanetActivity / VimsopakaBala / Dasa系统 / 综合预测

### 验证方法论

| 文件 | 内容 |
|------|------|
| `validation-methodology-batch-celebrity.md` | 批量名人验证方案 |
| `marriage-timing-validation-methodology.md` | 婚姻应期技法验证方法论 |
| `mandatory-verification-gate-protocol.md` | MEVG强制验证门控协议 |
| `verified-patterns-marriage-timing-v5.md` | 婚姻验证模式v5（含v5→v6重大Bug说明） |
| `verified-patterns-marriage-timing-v6.md` | 婚姻验证模式v6.1（18名人/26婚姻/66事件） |

### Bug 修复历史

`CHANGELOG.md` 中记录了 61 条 Bug 修复，关键修复包括：
- v6.0: UTC时区转换Bug（导致16/18案例上升星座错误）
- v4.3: Dasha浮点边界Bug
- v4.2: MEVG强制验证门控
- v3.7.2: Antardasha（次级大运）只为当前大运计算→改为全部9个大运
- v3.7.2: Moon Chesta Bala溢出（>60分上限）、Exalted D1分数、Paksha Bala归一化
