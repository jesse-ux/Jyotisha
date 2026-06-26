# Antigravity AI Sidecar Work Order Round 38

日期：2026-06-26  
范围：仅聚焦印度占星 skill 的技术成熟度、解释模板工业化、外部真值闭环和可合法复用资产，不以网页/app 外观为主。

## 本轮目标

把主线程 Codex 的算力集中在可直接编码的 skill 资产上；副手负责做高体量、低风险、强整理型侦察，减少主线程重复检索和上下文浪费。

## 工作包 A：文章来源与权威资料冲突矩阵

检查所有已纳入或候选纳入的文章级技法说明，逐条对照以下权威内部资料：

- `references/strict-workflow-router.md`
- `references/technique_registry.json`
- `references/deep-varga-avastha-execution-guide.md`
- `references/high-order-d9-execution-guide.md`
- `references/rtn-high-order-d9-freeze-execution-guide.md`
- 其他已存在 execution guide / freeze guide

输出：

- 一份 `article_authority_contradiction_matrix` 报告
- 标出哪些文章说法可直接吸收、哪些只能降级为灵感、哪些必须明确排除

## 工作包 B：下一批 12 个高价值解释模板排序

在当前已冻结的 9 个模板之外，列出最值得优先冻结的 12 个模板候选，按以下标准排序：

1. 对 skill 成熟度提升最大
2. 与现有 technique registry 覆盖形成闭环
3. 能减少“只会算、不够会解”的短板
4. 不依赖外部私有数据即可先完成边界冻结

每个候选模板必须给出：

- 模板 id 建议
- 主题名
- 主要触发词
- 需要的 cross-check
- 禁止越权的 claim
- 预期会依赖的本地 reference 文件

## 工作包 C：三大 external oracle 首包人工填写清单

分别针对以下三条闭环战线：

- Dasha external oracle
- Shadbala absolute values
- Tajika / Sahams annual oracle

输出每个 first packet 的：

- 缺失字段总数
- 字段名
- 单位
- 建议从 JHora / PyJHora 哪个页面、哪个区块读取
- 哪些字段属于 metadata，哪些属于 target

目标是让人类填第一包时不再二次猜测。

## 工作包 D：整机复用资产第六轮清查

再次扫描当前仓库、旧 skill 碎片和 `references/open_source_sources/`，重点找：

- Pushkara
- Vargottama
- Avastha
- RTN
- spouse / DK / UL
- wealth / Lakshmi / Dhana

要求：

- 只记录可合法复用的解释资产、常量、枚举、边界说明
- 明确排除 GPL/AGPL 代码本体复制
- 给出可直接被 Codex 吸收进 skill 的资产清单

## 工作包 E：给 Codex 的直接编码建议

基于以上四包，输出一份主线程友好的建议单：

- 只列 skill-first 的代码动作
- 每条动作要能在一个小 commit 内完成
- 优先级按 ROI 排序
- 明确哪些能立刻 TDD，哪些必须等待人类 external oracle 数据

## 交付物要求

至少生成以下 6 个文件到 `docs/research/`：

1. `antigravity_round38_article_authority_contradiction_matrix_2026_06_26.md`
2. `antigravity_round38_next12_template_rerank_2026_06_26.md`
3. `antigravity_round38_dasha_shadbala_tajika_first_packet_human_fill_map_2026_06_26.md`
4. `antigravity_round38_whole_machine_reuse_sixth_pass_2026_06_26.md`
5. `antigravity_round38_codex_round39_skill_first_top_tasks_2026_06_26.md`
6. 一份总览总结报告

## 成功标准

- 不重复泛泛而谈“还有很多任务”
- 每份报告都能直接服务下一轮编码
- 明确区分“可以现在做”和“必须等待 external_verified 人工数据”
