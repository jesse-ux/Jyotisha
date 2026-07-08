# Antigravity AI 副手任务单 Round 29（2026-06-26）

## 本轮唯一核心目标

不要再停留在“项目很强、还差产品化”这种泛结论。

Round 29 的唯一目标是：

**把当前印度占星 skill 离“本地即可直接测试全部核心技能与准确率”还差的部分，压缩成一批可直接执行、可复用、可验证、可同步到云端的重型任务包。**

副手这一轮要承担更多重活，减轻 Codex 主线程算力压力。你要尽量完成：

1. 全网黑盒对标。
2. 本机与历史仓库碎片复用盘点。
3. license 级别的可复制代码/常量筛选。
4. 现有 skill 本体、API、CLI、前端暴露差距拆解。
5. 外部 oracle 精度闭环的可执行清单。
6. 给 Codex 生成下一轮可直接 TDD 落地的 Top 120 任务。

## 当前必须承认的事实基线

你必须重新验证，不允许沿用旧印象：

- 当前主分支工作线仍在 `codex/release-hygiene-ci`。
- `references/technique_registry.json` 当前注册技法约为 `68`，并非“缺大量未注册技能”。
- 当前最可能拖后腿的不是“完全没有算法”，而是：
  - 已有技法未暴露到 API/CLI/前端；
  - 已有技法只有 covered，没有 complete；
  - 真实外部 oracle 数据依然太少；
  - 旧 skill / 本机碎片 / 历史 benchmark 未完全复用；
  - 主仓 skill 内容还未完全同步到用户更常直接使用的 skill 分发位置。
- 当前 repo 比旧 WorkBuddy skill 更新；旧 skill 不能反向覆盖主仓。
- Round 28 已经产出 30 份研究档，Round 29 必须建立在这些成果之上，不能重复空转。

## 副手工作边界

禁止：

- 不要修改 `scripts/`、`tests/`、`jyotish-app/`、`README.md`、`SKILL.md`、`references/` 现有逻辑文件。
- 不要提交、push、reset、rebase、删除、移动任何现有文件。
- 不要读取或回显任何 token、cookie、SSH 私钥、系统密钥内容。
- 不要复制 GPL / AGPL / LGPL / 闭源项目代码到建议中。
- 不要把 JHora / PyJHora / AstroSage / Drik Panchang 的黑盒输出假装成我们内部实现。

允许：

- 只新增 `docs/research/antigravity_round29_*_2026_06_26.md` 报告。
- 允许跑只读命令、测试、grep、联网搜索、license 检查、目录比对。
- 允许读取当前 repo、旧 WorkBuddy skill、`references/open_source_sources`、历史 rounds 文档、benchmarks、整机只读索引。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 16
git ls-remote https://github.com/732642856/yinduzhanxing.git 'refs/heads/codex/release-hygiene-ci' 'refs/heads/main'
python3 scripts/audit_capabilities.py --mode validate
python3 scripts/local_accuracy_report.py --format json
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
find . -maxdepth 3 -type f \( -name 'SKILL.md' -o -path './references/technique_registry.json' -o -path './references/strict-workflow-router.md' -o -path './skills/*/SKILL.md' \) | sort
find <home>/.workbuddy/skills/jyotish-vedic-astrology -maxdepth 3 -type f \( -name 'SKILL.md' -o -path '*/references/technique_registry.json' -o -path '*/references/strict-workflow-router.md' -o -path '*/skills/*/SKILL.md' \) 2>/dev/null | sort
rg -n "Tajika|Varshaphala|Chara Dasha|Kalachakra|Narayana|KP|Prashna|Shadbala|Bhava Bala|Ashtakavarga|Yoga Pinda|Varga|D60|D300|Pancha Pakshi|Saham|Ayanamsa|Porutham|Muhurta|Panchanga" SKILL.md README.md references scripts tests jyotish-app docs/research
rg -n "MIT|Apache|BSD|ISC|CC0|GPL|AGPL|LGPL|license|License|benchmark_only|copy_allowed|quarantine" references/open_source_sources docs/research <home>/.workbuddy/skills/jyotish-vedic-astrology/references 2>/dev/null
git diff --check
```

## 这一轮必须重点检查的对象

至少核查 50 个公开项目/产品/API 页面，并把结果汇总进报告中。必须包括：

1. PyJHora
2. Jagannatha Hora
3. VedAstro
4. VedAstro.Python / VedAstro API
5. Maitreya
6. kunjara/jyotish
7. jyotishganit
8. jyotisham/jyotisha
9. Hora Prakash
10. Drik Panchang
11. AstroSage
12. Prokerala
13. Astro-Seek
14. flatlib
15. xalen-ephemeris
16. dashaflow
17. panchanga_api
18. RoxyAPI jyotish app
19. KPAstroDashboard
20. Jaimini / KP / horary 相关开源仓库

其余 30 个由副手自主补足。

## Round 29 报告要求

至少产出 **24 份重型报告**，全部落入 `docs/research/`，文件名必须为：

- `docs/research/antigravity_round29_*_2026_06_26.md`

每份报告必须至少包含：

- 25 个以上检查点；
- 10 条以上可执行命令 / URL / 代码位置；
- 5 个以上 Codex 可直接 TDD 实现任务；
- 3 个以上可以继续丢给下一轮副手的任务；
- 1 个以上外部人工 oracle / 截图 / 黑盒验证任务；
- 明确状态：`已成立`、`部分成立`、`未成立`、`需要人工外部工具`、`license_blocked`。

## 工作包 A：Skill 全量补齐差距总表

输出：
`docs/research/antigravity_round29_skill_full_parity_gap_matrix_2026_06_26.md`

目标：

- 以“用户本地直接可用”为标准，不以“源码里存在函数”自欺。
- 对 68 个已注册技法逐项标注：
  - skill 已写明；
  - 后端可算；
  - API 可调；
  - CLI 可跑；
  - 前端可点；
  - 导出可见；
  - 测试存在；
  - 外部 oracle 存在；
  - 用户是否真的可理解结果。

## 工作包 B：covered -> complete 晋级优先级 Top 30

输出：
`docs/research/antigravity_round29_covered_to_complete_top30_2026_06_26.md`

## 工作包 C：API 未暴露能力总表

输出：
`docs/research/antigravity_round29_api_surface_missing_matrix_2026_06_26.md`

## 工作包 D：CLI 未暴露能力总表

输出：
`docs/research/antigravity_round29_cli_surface_missing_matrix_2026_06_26.md`

## 工作包 E：前端隐藏技能总表

输出：
`docs/research/antigravity_round29_frontend_hidden_skill_matrix_2026_06_26.md`

## 工作包 F：旧 Skill 与主仓同步差距

输出：
`docs/research/antigravity_round29_skill_sync_to_distribution_targets_2026_06_26.md`

## 工作包 G：整机碎片复用第二轮

输出：
`docs/research/antigravity_round29_whole_machine_fragment_reuse_second_pass_2026_06_26.md`

## 工作包 H：MIT/Apache 可直接复制资产 Top 50

输出：
`docs/research/antigravity_round29_copy_allowed_assets_top50_2026_06_26.md`

## 工作包 I：license quarantine 黑名单

输出：
`docs/research/antigravity_round29_license_quarantine_blacklist_2026_06_26.md`

## 工作包 J：最缺的 12 个“真新增技法”

输出：
`docs/research/antigravity_round29_true_missing_techniques_top12_2026_06_26.md`

## 工作包 K：外部 oracle 精度闭环路线

输出：
`docs/research/antigravity_round29_external_oracle_accuracy_closure_plan_2026_06_26.md`

## 工作包 L：Ayanamsa / ephemeris 精度差距

输出：
`docs/research/antigravity_round29_ayanamsa_ephemeris_accuracy_matrix_2026_06_26.md`

## 工作包 M：Tajika / Varshaphala 缺口总表

输出：
`docs/research/antigravity_round29_tajika_varshaphala_gap_matrix_2026_06_26.md`

## 工作包 N：Jaimini / KP / Prashna 缺口总表

输出：
`docs/research/antigravity_round29_jaimini_kp_prashna_gap_matrix_2026_06_26.md`

## 工作包 O：Panchanga / Muhurta 商业深度缺口

输出：
`docs/research/antigravity_round29_panchanga_muhurta_depth_gap_matrix_2026_06_26.md`

## 工作包 P：Synastry / Ashtakoot / Porutham 深度缺口

输出：
`docs/research/antigravity_round29_synastry_porutham_gap_matrix_2026_06_26.md`

## 工作包 Q：Shadbala / Bhava Bala / Ishta-Kashta 深度缺口

输出：
`docs/research/antigravity_round29_strength_system_gap_matrix_2026_06_26.md`

## 工作包 R：Varga / Avastha / 高阶分盘深度缺口

输出：
`docs/research/antigravity_round29_varga_avastha_gap_matrix_2026_06_26.md`

## 工作包 S：普通用户可用性缺口 Top 50

输出：
`docs/research/antigravity_round29_local_user_experience_top50_2026_06_26.md`

## 工作包 T：云端同步白名单计划

输出：
`docs/research/antigravity_round29_cloud_sync_whitelist_plan_2026_06_26.md`

## 工作包 U：Codex Round 30 Top 120

输出：
`docs/research/antigravity_round29_codex_round30_top120_2026_06_26.md`

## 工作包 V：最终总报告

输出：
`docs/research/antigravity_round29_final_execution_ranking_2026_06_26.md`

必须明确回答：

1. 当前离“本地可直接测试全部核心技能”还差多少块。
2. 当前离“对标应用所有核心技能”还差多少真新增技法。
3. 当前离“解盘精准度可实测”还差多少外部 oracle。
4. 还有多少问题只是同步/暴露/产品化，而不是算法缺失。
5. Codex 下一轮最应该先做哪 20 件事。
6. 哪些任务必须继续压给副手。

## 额外要求：副手自选 4 份加压报告

在完成上述 22 个工作包后，再自选至少 4 个你判断 Codex 最容易遗漏、但会直接影响“全技能 + 精度 + 本地可用性”的主题，产出额外报告。

## 本轮状态定义

只有当你真正把“技能缺口、复用来源、云端同步、精度闭环、可执行任务”五条线都压缩成可执行文档矩阵后，才能写：

`已成立`

否则必须老实写：

`部分成立`
