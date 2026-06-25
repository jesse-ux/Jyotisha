# Antigravity AI 副手任务单 Round 28（2026-06-26）

## 总目标

本轮不要再泛泛说“还缺产品化”。用户的新目标是：

**评估并规划如何让当前印度占星 skill 在“技法广度 + 传统软件深度 + AI 证据链解盘 + 中文产品体验”上冲击全球开源第一。**

副手负责重活：

1. 全网对标 PyJHora/JHora/VedAstro/Maitreya/jyotishganit/kunjara/Hora Prakash/panchanga 等。
2. 地毯式检查本机旧 skill、历史仓库、open_source_sources、benchmarks 是否已有可复用技法。
3. 把“需要新增技法”与“已有但未产品化/未校准/未同步”严格分开。
4. 所有可复用代码必须先查 license；MIT/Apache/BSD/ISC/CC0 才能列为可复制候选。
5. 产出 Codex 可直接 TDD 实现的 Top 100 任务。

## 当前事实基线

必须重新验证，不要沿用旧结论：

- 远端分支 `codex/release-hygiene-ci` 已推到 `6a31461`。
- `references/technique_registry.json` 当前注册 `68` 技法，`complete=10`、`covered=58`、`missing=0`、`partial=0`。
- 当前并不是“缺大量 skill 注册项”，而是：
  - covered -> complete 的升级；
  - 后端/API/前端/导出/AI Prompt Pack 的可见性；
  - 外部 oracle 校准；
  - 对标传统软件的长尾技法深度；
  - 云端/skill 本体同步。
- 主仓当前比旧 WorkBuddy skill 更新；不要用旧 skill 覆盖主仓。
- 复用索引已存在：`docs/research/local_reuse_candidate_index_round28_2026_06_26.md`。

## 严格边界

禁止：

- 不要修改 `scripts/`、`tests/`、`jyotish-app/`、`README.md`、`SKILL.md`、`references/`。
- 不要提交、推送、删除、重置、移动文件。
- 不要读取或传播 token、API key、cookie、SSH 私钥、系统钥匙串。
- 不要提交用户私人 PDF、Obsidian 原文、Downloads 原文。
- 不要复制 GPL/AGPL/LGPL/闭源代码。
- 不要把 PyJHora/JHora/AstroSage 输出写成我们自己的内部计算实现。

允许：

- 只能新增 `docs/research/*round28*2026_06_26.md` 报告文件。
- 可以运行只读命令、测试、grep、联网检索、license 检查。
- 可以读取旧 skill、历史 benchmark、open_source_sources、Round25-27 报告。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 12
git ls-remote https://github.com/732642856/yinduzhanxing.git 'refs/heads/codex/release-hygiene-ci' 'refs/heads/main'
python3 scripts/audit_capabilities.py --mode validate
python3 scripts/local_accuracy_report.py --format json
python3 scripts/local_accuracy_report.py --format markdown
find . -maxdepth 3 -type f \( -name 'SKILL.md' -o -path './references/technique_registry.json' -o -path './references/strict-workflow-router.md' -o -path './skills/*/SKILL.md' \) | sort
find /Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology -maxdepth 3 -type f \( -name 'SKILL.md' -o -path '*/references/technique_registry.json' -o -path '*/references/strict-workflow-router.md' -o -path '*/skills/*/SKILL.md' \) 2>/dev/null | sort
rg -n "Dasha|dasha|Panchanga|Muhurta|Ashtakoot|Porutham|Shadbala|Avastha|Jaimini|KP|Prashna|Remedies|Saham|Pancha Pakshi|D60|D300|Yoga|Dosha|rectification" SKILL.md README.md references scripts tests docs/research
rg -n "MIT|Apache|BSD|ISC|CC0|GPL|AGPL|LGPL|License|license|benchmark_only|copy_allowed|do_not_use" references/open_source_sources docs/research /Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology/references 2>/dev/null
git diff --check
```

## 联网对标必查对象

至少查 40 个公开项目/产品页面，其中必须包括：

1. PyJHora / naturalstupid/PyJHora
2. Jagannatha Hora
3. VedAstro/VedAstro
4. VedAstro.Python 或 VedAstro API 文档
5. Maitreya
6. kunjara/jyotish
7. jyotishganit
8. jyotisham/jyotisha
9. Hora Prakash
10. RoxyAPI jyotish app
11. RaviKarrii Marriage Compatibility
12. dashaflow
13. panchanga_api
14. xalen-ephemeris
15. flatlib
16. kerykeion（仅 UI/图形参考）
17. Drik Panchang
18. AstroSage
19. Prokerala
20. Astro-Seek Vedic pages

其余 20 个由副手补足。

## 报告数量要求

至少产出 **30 份 Round28 报告**，全部写入 `docs/research/`，文件名必须含 `antigravity_round28_*_2026_06_26.md`。

每份报告必须包含：

- 至少 30 个检查点。
- 至少 12 条可复制命令、URL、文件路径或代码位置。
- 至少 5 个 Codex 可直接 TDD 实现的任务。
- 至少 3 个可由副手下一轮继续做的任务。
- 至少 1 个人工外部 oracle 任务。
- 明确状态：`已成立`、`部分成立`、`未成立`、`需要人工外部工具`、`license_blocked`。

## 工作包 A：全球开源 Jyotish 排名证据表

输出：`docs/research/antigravity_round28_global_open_source_rank_evidence_2026_06_26.md`

比较当前项目与 PyJHora、VedAstro、Maitreya、jyotishganit、kunjara、Hora Prakash 等，按：

- 技法广度
- 传统深度
- API/web 产品化
- AI 解盘能力
- 中文体验
- 测试/benchmark
- license 可复用性
- 外部 oracle

给出保守排名和冲第一路径。

## 工作包 B：PyJHora/JHora 技法广度差距表

输出：`docs/research/antigravity_round28_pyjhora_jhora_breadth_gap_matrix_2026_06_26.md`

列出 PyJHora/JHora 有而本项目未完整产品化的技法，分类为：

- 已有且可见
- 已有但隐藏
- 已有但未校准
- 未登记新技法
- GPL/AGPL 只能黑盒

## 工作包 C：VedAstro/MIT 可复制资产清单

输出：`docs/research/antigravity_round28_vedastro_mit_copy_candidates_2026_06_26.md`

列具体文件、license、可复制常量/矩阵/测试、不可复制风险、NOTICE 要求。

## 工作包 D：Dasha 系统冲第一路线

输出：`docs/research/antigravity_round28_dasha_35_to_pyjhora_parity_plan_2026_06_26.md`

比较 Vimshottari、Ashtottari、Yogini、Kalachakra、Narayana、conditional dashas、Jaimini dashas、Bhrigu Pada 等，列 Top 30 缺口。

## 工作包 E：Panchanga/Calendar 商业深度路线

输出：`docs/research/antigravity_round28_panchanga_depth_to_drik_parity_plan_2026_06_26.md`

目标对标 Drik Panchang/AstroSage/Prokerala，列 festival、vrata、karana、nitya yoga、tarabala、chandrabala、choghadiya、hora、Rahu/Yama/Gulika、ICS 订阅等缺口。

## 工作包 F：Muhurta 深度路线

输出：`docs/research/antigravity_round28_muhurta_depth_plan_2026_06_26.md`

列活动类型、过滤层、个人化 Tarabala/Chandrabala、婚礼/商业/旅行/医疗/搬家等标准。

## 工作包 G：Ashtakoot/Porutham/合婚深度路线

输出：`docs/research/antigravity_round28_synastry_depth_plan_2026_06_26.md`

比较 Ashtakoot 8、Porutham 10、Kuja/Mangal、Papasamya、Rajju、Vedha、Mahendra、Strii Deergha。

## 工作包 H：Shadbala/力量体系深度路线

输出：`docs/research/antigravity_round28_shadbala_strength_depth_plan_2026_06_26.md`

比较 Sthana/Dig/Kala/Chesta/Naisargika/Drik、Ishta/Kashta、Bhava Bala、Vimsopaka、Avastha。

## 工作包 I：Jaimini/KP/Prashna 深度路线

输出：`docs/research/antigravity_round28_jaimini_kp_prashna_depth_plan_2026_06_26.md`

列 Chara Karaka、Arudha、Argala、Special Lagnas、KP 249 sublord、Prashna judgement。

## 工作包 J：Varga/D1-D300 深度路线

输出：`docs/research/antigravity_round28_varga_d1_d300_depth_plan_2026_06_26.md`

比较 D1-D60、D81/D108/D144/D150/D300、自定义 D-N、D-mxn 复合分盘。

## 工作包 K：Yoga/Dosha/Remedies 深度路线

输出：`docs/research/antigravity_round28_yoga_dosha_remedies_depth_plan_2026_06_26.md`

列 Yoga 405+、PyJHora 100+ 对照、Dosha、Remedies、Gemstone、Mantra、Donation、Fast。

## 工作包 L：AI 解盘第一路线

输出：`docs/research/antigravity_round28_ai_native_reading_rank1_plan_2026_06_26.md`

目标不是只算表格，而是超过传统软件的 AI 证据链解盘；列 prompt pack、RAG、Technique Audit Table、置信度、反证、用户语言体验。

## 工作包 M：Skill 本体同步缺口

输出：`docs/research/antigravity_round28_skill_sync_gap_audit_2026_06_26.md`

比较主仓 `SKILL.md` 与旧 WorkBuddy skill，确认哪些旧内容已过期、哪些主仓新内容必须保持云端同步。

## 工作包 N：当前项目“真新增技法”最小清单

输出：`docs/research/antigravity_round28_true_new_technique_minimum_set_2026_06_26.md`

排除已有 covered/complete 后，只列真正值得新增登记的技法。

## 工作包 O：covered -> complete 晋级清单

输出：`docs/research/antigravity_round28_covered_to_complete_upgrade_plan_2026_06_26.md`

列 58 个 covered 里最该升级 complete 的 Top 25，每项含测试和用户可见入口。

## 工作包 P：前端产品化冲刺 Top 50

输出：`docs/research/antigravity_round28_frontend_productization_top50_2026_06_26.md`

围绕普通用户能点、能导出、能理解。

## 工作包 Q：API/CLI 暴露冲刺 Top 50

输出：`docs/research/antigravity_round28_api_cli_exposure_top50_2026_06_26.md`

围绕本地电脑可直接使用。

## 工作包 R：外部 oracle 样本 Top 50

输出：`docs/research/antigravity_round28_external_oracle_sample_top50_2026_06_26.md`

按 Dasha/Shadbala/Ashtakoot/Panchanga/Muhurta/Varga/Yoga 排优先级。

## 工作包 S：Codex Round29 Top 100 执行清单

输出：`docs/research/antigravity_round28_codex_round29_top100_2026_06_26.md`

每项含：文件、测试、验收、复用来源、license、是否需人工。

## 工作包 T：最终总报告

输出：`docs/research/antigravity_round28_final_summary_rank1_strategy_2026_06_26.md`

必须回答：

1. 当前项目全球开源排名如何。
2. 能否冲第一。
3. 最少需要多少轮。
4. 需要新增多少真技法。
5. 需要产品化多少已有技法。
6. 需要多少外部 oracle。
7. 下一轮 Codex 先干什么。

## 额外 10 份自选报告

副手必须再补 10 份自选报告，覆盖它认为 Codex 最容易遗漏的深水区。
