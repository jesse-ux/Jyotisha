# Antigravity AI 副手任务单 Round 30（2026-06-26）

## 本轮目标

Round 30 不再泛化讨论“还差产品化”。

这一轮只做三类重活，替 Codex 减负：

1. 把 Round 29 的 28 份报告进一步压缩为 **可执行、可同步、可验证** 的落地矩阵。
2. 地毯式继续核查 **云端同步白名单 / skill 分发位置 / 本机碎片**，避免主仓修好了、用户常用 skill 入口还是旧的。
3. 深挖 **外部 oracle / 本地可测试准确率 / CLI 与前端暴露** 的下一批最高 ROI 任务。

## 严格边界

禁止：

- 不要修改任何 `scripts/`、`tests/`、`jyotish-app/`、`README.md`、`SKILL.md`、`references/` 逻辑文件。
- 不要 push / commit / reset / rebase / 删除 / 移动文件。
- 不要读取或泄露 token、cookie、SSH 私钥、系统密钥。
- 不要把 GPL / AGPL / LGPL / 闭源代码列入“可直接复制”。

允许：

- 只新增 `docs/research/antigravity_round30_*_2026_06_26.md`。
- 运行只读命令、测试、联网检索、license 检查、目录比对。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 20
git ls-remote https://github.com/732642856/yinduzhanxing.git 'refs/heads/codex/release-hygiene-ci' 'refs/heads/main'
python3 scripts/audit_capabilities.py --mode validate
python3 scripts/local_accuracy_report.py --format json
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
find . -maxdepth 3 -type f \( -name 'SKILL.md' -o -path './references/technique_registry.json' -o -path './references/strict-workflow-router.md' -o -path './skills/*/SKILL.md' \) | sort
find <home>/.workbuddy/skills/jyotish-vedic-astrology -maxdepth 3 -type f \( -name 'SKILL.md' -o -path '*/references/technique_registry.json' -o -path '*/references/strict-workflow-router.md' -o -path '*/skills/*/SKILL.md' \) 2>/dev/null | sort
rg -n "table|tabulate|Tajika|Varshaphala|Jaimini|Chara Dasha|Shadbala|Ashtakavarga|Panchanga|Muhurta|Porutham|Ayanamsa|oracle|external_verified|artifacts" SKILL.md README.md references scripts tests jyotish-app docs/research
rg -n "MIT|Apache|BSD|ISC|CC0|GPL|AGPL|LGPL|license|License|quarantine|copy_allowed" references/open_source_sources docs/research <home>/.workbuddy/skills/jyotish-vedic-astrology/references 2>/dev/null
git diff --check
```

## 本轮至少产出 18 份报告

全部写入 `docs/research/`，文件名必须为：

- `docs/research/antigravity_round30_*_2026_06_26.md`

每份报告至少包含：

- 20 个检查点；
- 8 条命令 / URL / 文件路径；
- 5 条 Codex 可直接执行任务；
- 2 条继续交给下一轮副手的任务；
- 1 条人工 oracle / 黑盒验证任务；
- 状态结论：`已成立`、`部分成立`、`未成立`、`需要人工外部工具`、`license_blocked`。

## 工作包

### A. Round 29 压缩执行矩阵
输出：`antigravity_round30_round29_condensed_execution_matrix_2026_06_26.md`

把 28 份 Round 29 报告压缩成一个真正能指导开发顺序的矩阵。

### B. 云端同步白名单二次审计
输出：`antigravity_round30_cloud_sync_whitelist_second_pass_2026_06_26.md`

明确：
- 主仓哪些文件应同步到云端；
- 哪些研究应归档；
- 哪些 skill 分发位置要更新；
- 哪些 build/cache/log 绝不能进仓。

### C. Skill 分发目标实地盘点
输出：`antigravity_round30_skill_distribution_targets_inventory_2026_06_26.md`

列出主仓外所有高相关 skill 分发位置与优先级。

### D. WorkBuddy 覆盖白名单
输出：`antigravity_round30_workbuddy_sync_whitelist_2026_06_26.md`

不要泛泛而谈，要精确到文件级别。

### E. 本地可测试准确率 Top 30 阻塞点
输出：`antigravity_round30_local_accuracy_blockers_top30_2026_06_26.md`

从“我现在本地要测准确率”的角度，只列真正阻碍用户测试的点。

### F. CLI Productization Top 30
输出：`antigravity_round30_cli_productization_top30_2026_06_26.md`

重点核查：
- `--table`
- 可读表格
- 对比输出
- 合婚 CLI
- Panchanga / Muhurta CLI
- 错误信息是否人类可懂

### G. Frontend 高 ROI 暴露 Top 30
输出：`antigravity_round30_frontend_exposure_top30_2026_06_26.md`

不要发散，只列“后端已存在，前端一加就有感知”的点。

### H. API 高 ROI 暴露 Top 30
输出：`antigravity_round30_api_exposure_top30_2026_06_26.md`

### I. 外部 Oracle 样本任务清单 Top 40
输出：`antigravity_round30_external_oracle_tasks_top40_2026_06_26.md`

### J. MIT 可复制资产再筛选
输出：`antigravity_round30_copy_allowed_assets_second_pass_2026_06_26.md`

### K. License 隔离墙复核
输出：`antigravity_round30_license_quarantine_recheck_2026_06_26.md`

### L. Tajika / Jaimini / Shadbala / Ashtakavarga 用户可见性复核
输出：`antigravity_round30_visibility_blackbox_for_high_roi_modules_2026_06_26.md`

### M. 整机碎片第三轮复用排查
输出：`antigravity_round30_whole_machine_fragment_reuse_third_pass_2026_06_26.md`

### N. Codex Round 31 Top 150
输出：`antigravity_round30_codex_round31_top150_2026_06_26.md`

### O. 最终执行总报告
输出：`antigravity_round30_final_execution_board_2026_06_26.md`

必须回答：
1. 哪些工作今天就该由 Codex 直接写代码完成。
2. 哪些必须继续压给副手。
3. 哪些必须等待人工外部 oracle。
4. 哪些只是同步工作，不是算法工作。
5. 哪些对“本地立即可测准确率”最关键。

## 额外 3 份自选报告

副手必须再自选 3 个它认为最容易被忽略、但直接影响“本地可用性 + skill 同步 + 准确率验证”的主题。

## 状态定义

只有当报告真正把“同步、分发、复用、验证、可执行任务”五条线压缩成开发顺序矩阵时，才能写：

`已成立`

否则必须写：

`部分成立`
