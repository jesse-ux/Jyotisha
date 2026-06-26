# Antigravity AI 副手任务单 Round 31（2026-06-26）

## 本轮目标

Round 31 继续为 Codex 减负，但不再泛泛做“差距盘点”。

本轮只做三件大事：

1. 地毯式继续扫描整机与分发位置，找出还能直接复用或必须合并的印度占星 skill / 文档 / technique registry 碎片。
2. 全网继续检索可合法复用的 MIT / Apache / BSD / ISC / CC0 印度占星开源资产，输出可直接搬运的优先级清单。
3. 把“本地可立即测试准确率”这条主线继续压缩成最短执行路径，尤其是 CLI、API、前端、oracle 样本、Ayanamsa/ephemeris 精度这五条线。

## 严格边界

禁止：

- 不要修改任何 `scripts/`、`tests/`、`jyotish-app/`、`README.md`、`SKILL.md`、`references/`、`.gitignore`。
- 不要 push / commit / rebase / reset / stash / 删除 / 移动文件。
- 不要输出任何 token、cookie、SSH 私钥、浏览器本地凭证、系统账号隐私。
- 不要把 GPL / AGPL / LGPL / 闭源代码判定为“可直接复制”。

允许：

- 只新增 `docs/research/antigravity_round31_*_2026_06_26.md`
- 运行只读命令、联网检索、license 检查、目录扫描、黑盒测试、对比分析。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 25
git ls-remote ssh://git@ssh.github.com:443/732642856/yinduzhanxing.git 'refs/heads/codex/release-hygiene-ci' 'refs/heads/main'
python3 scripts/audit_capabilities.py --mode validate
python3 scripts/local_accuracy_report.py --format json
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
find . -maxdepth 4 -type f \( -name 'SKILL.md' -o -path './references/technique_registry.json' -o -path './references/strict-workflow-router.md' -o -path './skills/*/SKILL.md' \) | sort
find /Users/wuyongnaren/.workbuddy -maxdepth 5 -type f \( -name 'SKILL.md' -o -path '*/technique_registry.json' -o -path '*/strict-workflow-router.md' \) 2>/dev/null | sort
find /Users/wuyongnaren -maxdepth 6 -type f \( -name 'SKILL.md' -o -name 'technique_registry.json' -o -name 'strict-workflow-router.md' \) 2>/dev/null | rg "jyotish|vedic|占星|印度占星|workbuddy|skill"
rg -n "Tajika|Varshaphala|Jaimini|Chara Dasha|Narayana|Kalachakra|KP|Prashna|Shadbala|Bhava Bala|Ashtakavarga|Yoga Pinda|Panchanga|Muhurta|Porutham|Synastry|Ayanamsa|oracle|external_verified|artifacts|table|tabulate" SKILL.md README.md references scripts tests jyotish-app docs/research
rg -n "MIT|Apache|BSD|ISC|CC0|GPL|AGPL|LGPL|license|License|quarantine|copy_allowed|benchmark_only" references/open_source_sources docs/research /Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology/references 2>/dev/null
git diff --check
```

## 本轮至少产出 20 份报告

全部写入 `docs/research/`，命名必须为：

- `docs/research/antigravity_round31_*_2026_06_26.md`

每份报告至少包含：

- 25 个检查点
- 10 条命令 / URL / 文件路径
- 8 条 Codex 可直接执行任务
- 3 条适合继续下压给下一轮副手的任务
- 1 条必须人工外部 oracle / JHora / PyJHora / 真实截图参与的任务
- 1 个明确状态：`已成立` / `部分成立` / `未成立` / `需要人工外部工具` / `license_blocked`

## 指定工作包

### A. 主仓 vs WorkBuddy vs 全机碎片第四轮对照总表
输出：`antigravity_round31_whole_machine_fragment_reuse_fourth_pass_2026_06_26.md`

必须回答：
- 还有没有新的 skill/registry/router 碎片
- 哪些是真重复
- 哪些是旧版但仍被用户入口引用
- 哪些应进入同步白名单

### B. Skill 单一事实源执行守则复核
输出：`antigravity_round31_single_source_of_truth_enforcement_2026_06_26.md`

### C. 可合法复制资产 Top 80
输出：`antigravity_round31_copy_allowed_assets_top80_2026_06_26.md`

要求：
- 只收 MIT / Apache / BSD / ISC / CC0
- 精确到仓库、文件、常数表、数据表、文档表
- 按“可直接复制 / 可改写引用 / 仅可 benchmark”分层

### D. License 高压线黑名单 Top 60
输出：`antigravity_round31_license_quarantine_blacklist_top60_2026_06_26.md`

### E. 本地立即测准确率最短路径 Top 50
输出：`antigravity_round31_local_accuracy_shortest_path_top50_2026_06_26.md`

重点只看：
- 当前本地电脑上马上能跑什么
- 哪些阻塞必须先解决
- 哪些任务对“我现在开始测精度”没有帮助，应该后移

### F. CLI 能力补完 Top 50
输出：`antigravity_round31_cli_completion_top50_2026_06_26.md`

重点核查：
- 哪些命令已有后端但 CLI 可读性差
- 哪些最值得继续补 `--table`
- 哪些错误提示对普通用户不友好

### G. API 暴露补完 Top 50
输出：`antigravity_round31_api_completion_top50_2026_06_26.md`

### H. 前端暴露补完 Top 50
输出：`antigravity_round31_frontend_completion_top50_2026_06_26.md`

### I. 高优先级传统技法缺口复核
输出：`antigravity_round31_true_missing_traditional_techniques_top30_2026_06_26.md`

重点覆盖：
- Tajika / Varshaphala 深度
- Jaimini dasha
- KP / Prashna
- Panchanga / Muhurta 深度
- Porutham / Synastry 深度
- Strength systems beyond Shadbala

### J. Ayanamsa / Ephemeris / 历史时区精度风险矩阵
输出：`antigravity_round31_ayanamsa_ephemeris_timezone_risk_matrix_2026_06_26.md`

### K. Oracle 样本闭环 Top 60
输出：`antigravity_round31_external_oracle_closure_top60_2026_06_26.md`

### L. JHora / PyJHora 真实截图执行手册复核
输出：`antigravity_round31_jhora_pyjhora_capture_manual_review_2026_06_26.md`

### M. 云端仓库同步白名单终稿建议
输出：`antigravity_round31_cloud_sync_whitelist_final_draft_2026_06_26.md`

### N. 用户本地使用体验 Top 60
输出：`antigravity_round31_local_user_experience_top60_2026_06_26.md`

### O. Codex Round 32 Top 180
输出：`antigravity_round31_codex_round32_top180_2026_06_26.md`

### P. 最终执行总板
输出：`antigravity_round31_final_execution_board_2026_06_26.md`

必须明确：
1. 哪 20 项最该由 Codex 直接写代码
2. 哪 20 项继续压给副手
3. 哪些必须等待人工真实截图 / 外部 oracle
4. 哪些只是同步 / 分发 / 整理工作
5. 哪些最能提升“本地立即测试准确率”

## 额外重型要求

副手除以上指定工作包外，还必须自选 4 份“最容易被忽略但高影响”的补充报告。

这些补充报告必须围绕：

- 整机碎片复用
- 云端 / 本地 skill 一致性
- 可合法复制资产
- 本地可测准确率闭环

## 状态定义

只有当报告真正把“同步、分发、复用、可复制资产、可执行任务、人工 oracle 闭环”压成开发顺序，才能写：

`已成立`

否则只能写：

`部分成立` / `未成立` / `需要人工外部工具` / `license_blocked`
