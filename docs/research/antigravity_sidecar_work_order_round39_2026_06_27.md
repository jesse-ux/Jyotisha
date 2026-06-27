# Antigravity AI Sidecar Work Order - Round 39 - 2026-06-27

## Mission

本轮继续只服务印度占星 `skill` 主线，不做网页/app 外观工作，不改核心源码。目标是替主线程进一步压缩“全球第一 skill”还缺的硬情报，尤其围绕：

1. PyJHora black-box 资产继续扩充
2. VedAstro service adapter 对接前的字段映射与公开契约核查
3. Dasha / Shadbala / Tajika 三大战线的真实 external oracle 首包之后的第二批优先级
4. 文章级解释模板的权威降噪
5. 长期 benchmark 护城河的公开字段设计

## Hard Constraints

- 不修改主仓核心实现代码。
- 只做研究、检索、黑盒比对、任务拆解、资料整理。
- 必须优先复用现有 `docs/research/`、`references/oracle/`、`references/open_source_sources/` 资料。
- AGPL / GPL 只允许 black-box、stdout、字段映射、行为观察，不允许建议复制代码实现。
- 每份报告必须能直接减少 Codex 下一轮的上下文浪费。

## Work Packages

### A. PyJHora black-box asset expansion board

目标：

- 基于现有 `references/oracle/artifacts/` 和 `pending_packets/`，列出下一批最值得补抓的 12 个 PyJHora black-box 资产。
- 优先级偏向：
  - Chara Dasha
  - Kalachakra Dasha
  - Ashtakavarga / SAV / BAV
  - Bhava Bala
  - Special Lagnas
  - Vargottama / Pushkara / Avastha 边界例子

输出：
- `antigravity_round39_pyjhora_blackbox_asset_expansion_board_2026_06_27.md`

### B. VedAstro request/response mapping audit

目标：

- 只研究 VedAstro 作为 service adapter candidate 时，哪些字段和我们本地 contract 已对齐，哪些还缺中间映射层。
- 明确：
  - ayanamsa policy
  - node policy
  - body naming
  - divisional chart identifiers
  - dasha naming
  - timezone / DST expectations

输出：
- `antigravity_round39_vedastro_mapping_audit_2026_06_27.md`

### C. Three-front second-wave packet rerank

目标：

- 在 Dasha / Shadbala / Tajika 三大战线里，不再讨论 first packet，而是排出 second-wave 的前 15 个 packet。
- 每个 packet 说明：
  - 为什么它是 second-wave 高 ROI
  - 需要人类录入还是可以先靠公开书例
  - 对 skill 精度和“全球第一”目标的实际贡献

输出：
- `antigravity_round39_three_front_second_wave_packets_2026_06_27.md`

### D. Authority-first article template truth cleanup

目标：

- 把近几轮用户补充的文章、截图线索里，容易误导的说法筛一遍。
- 特别检查：
  - 财富点 / Lakshmi / Dhana
  - DK / UL / spouse elevation
  - 上升度数 / 紧密合相
  - Nakshatra 天赋标签
  - 工作时间预测

输出：
- `antigravity_round39_article_truth_cleanup_2026_06_27.md`

### E. Public benchmark schema v2 board

目标：

- 设计一个别人难以短期追上的公开 benchmark 字段体系。
- 不是产品方案，而是字段和数据制度方案：
  - case metadata
  - external evidence provenance
  - tolerance policy
  - ayanamsa / node / timezone normalization
  - explanation-template scoring

输出：
- `antigravity_round39_public_benchmark_schema_v2_2026_06_27.md`

### F. Codex direct top 80

目标：

- 基于以上 5 包，为主线程输出只服务 skill 的 Top 80 下一步动作。
- 每条动作必须标记：
  - `doc_freeze`
  - `tdd_now`
  - `needs_human_oracle`
  - `blocked_by_license`

输出：
- `antigravity_round39_codex_round40_skill_top80_2026_06_27.md`

## Deliverables

至少生成以下 6 个文件到 `docs/research/`：

1. `antigravity_round39_pyjhora_blackbox_asset_expansion_board_2026_06_27.md`
2. `antigravity_round39_vedastro_mapping_audit_2026_06_27.md`
3. `antigravity_round39_three_front_second_wave_packets_2026_06_27.md`
4. `antigravity_round39_article_truth_cleanup_2026_06_27.md`
5. `antigravity_round39_public_benchmark_schema_v2_2026_06_27.md`
6. `antigravity_round39_codex_round40_skill_top80_2026_06_27.md`

## Success Standard

- 不重复“还有很多 gap”这种空话。
- 每份报告都能直接节省 Codex 下一轮时间。
- 明确区分：
  - 现在可直接编码
  - 现在只能文档冻结
  - 必须等待人类 external oracle
  - 受许可证隔离，只能 black-box
