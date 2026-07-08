# Antigravity AI 副手任务单 Round 32（2026-06-26）

## 本轮目标

Round 32 不再重复做能力清点。

这一轮只做三类“直接减轻 Codex 主线算力和注意力负担”的重任务：

1. 把已有报告压缩成 **代码可执行清单**，尤其是 API / CLI / 前端 / 同步 / oracle 五条线。
2. 按“本地立即可测准确率”优先级，给出 **最短开发路径与最短人工验证路径**。
3. 继续全网检索和本机复用，找出 **可以合法直接复制** 的高 ROI 常量、数据表、接口设计与非 GPL 文档结构。

## 严格边界

禁止：

- 不要修改任何 `scripts/`、`tests/`、`jyotish-app/`、`README.md`、`SKILL.md`、`references/`、`.gitignore`。
- 不要 push / commit / rebase / reset / stash / 删除 / 移动任何文件。
- 不要输出任何 token、cookie、SSH 私钥、浏览器本地凭证、系统账号隐私。
- 不要把 GPL / AGPL / LGPL / 闭源代码列入可直接复制区。

允许：

- 只新增 `docs/research/antigravity_round32_*_2026_06_26.md`
- 运行只读命令、联网检索、license 检查、目录扫描、黑盒测试、对照分析。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 30
git ls-remote ssh://git@ssh.github.com:443/732642856/yinduzhanxing.git 'refs/heads/codex/release-hygiene-ci' 'refs/heads/main'
python3 scripts/audit_capabilities.py --mode validate
python3 scripts/local_accuracy_report.py --format json
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
find . -maxdepth 4 -type f \( -name 'SKILL.md' -o -path './references/technique_registry.json' -o -path './references/strict-workflow-router.md' -o -path './skills/*/SKILL.md' \) | sort
find <home>/.workbuddy -maxdepth 6 -type f \( -name 'SKILL.md' -o -name 'technique_registry.json' -o -name 'strict-workflow-router.md' \) 2>/dev/null | sort
find <home> -maxdepth 7 -type f \( -name 'SKILL.md' -o -name 'technique_registry.json' -o -name 'strict-workflow-router.md' \) 2>/dev/null | rg "jyotish|vedic|占星|印度占星|workbuddy|skill"
rg -n "Tajika|Varshaphala|Jaimini|Chara Dasha|Narayana|Kalachakra|KP|Prashna|Shadbala|Bhava Bala|Ashtakavarga|Yoga Pinda|Panchanga|Muhurta|Porutham|Synastry|Ayanamsa|oracle|external_verified|artifacts|table|tabulate|timezone|DST|polar" SKILL.md README.md references scripts tests jyotish-app docs/research
rg -n "MIT|Apache|BSD|ISC|CC0|GPL|AGPL|LGPL|license|License|quarantine|copy_allowed|benchmark_only" references/open_source_sources docs/research <home>/.workbuddy/skills/jyotish-vedic-astrology/references 2>/dev/null
git diff --check
```

## 本轮至少产出 18 份报告

全部写入 `docs/research/`，命名必须为：

- `docs/research/antigravity_round32_*_2026_06_26.md`

每份报告至少包含：

- 25 个检查点
- 10 条命令 / URL / 文件路径
- 10 条 Codex 可直接执行任务
- 3 条继续交给下一轮副手的任务
- 1 条必须人工外部 oracle / JHora / PyJHora / 真实截图参与的任务
- 1 个明确状态：`已成立` / `部分成立` / `未成立` / `需要人工外部工具` / `license_blocked`

## 指定工作包

### A. API 直接编码任务 Top 40
输出：`antigravity_round32_api_direct_coding_top40_2026_06_26.md`

要求：
- 每条都必须精确到 endpoint、payload、预期响应字段、对应测试文件。
- 特别关注 `/api/dasha/chara`、`/api/tajika`、`/api/muhurta`、`/api/varga_full`、`/api/jaimini`。

### B. CLI 直接编码任务 Top 40
输出：`antigravity_round32_cli_direct_coding_top40_2026_06_26.md`

重点：
- 哪些命令最该补 `--table`
- 哪些 CLI 错误信息最该做人类可读化
- 哪些命令本地测试价值最高

### C. 前端直接编码任务 Top 40
输出：`antigravity_round32_frontend_direct_coding_top40_2026_06_26.md`

重点：
- 后端已存在、但前端还没暴露的高 ROI 技能
- 哪些最能让用户立刻感知“能力完整”

### D. 云端/本地/WorkBuddy 同步执行脚本建议
输出：`antigravity_round32_sync_script_blueprint_2026_06_26.md`

要求：
- 给出 `rsync` / `ln -sf` / 白名单同步建议
- 明确哪些文件必须同步，哪些必须排除
- 严禁建议同步源码缓存、日志、测试输出、dist 垃圾

### E. MIT 可直接搬运代码资产 Top 100
输出：`antigravity_round32_copy_allowed_assets_top100_2026_06_26.md`

要求：
- 精确到仓库、文件、函数、常量、数据表、API schema
- 每项都给出 license 判断和用途

### F. GPL/AGPL/LGPL 黑名单隔离复核
输出：`antigravity_round32_license_blacklist_recheck_2026_06_26.md`

### G. 本地立即测准确率最短链路终稿
输出：`antigravity_round32_local_accuracy_shortest_chain_final_2026_06_26.md`

要求：
- 只保留真正影响“今天就测”的事项
- 把无关项全部后移

### H. 真实 oracle 样本推进矩阵
输出：`antigravity_round32_oracle_sample_push_matrix_2026_06_26.md`

### I. JHora / PyJHora 截图与人工录入流程压缩版
输出：`antigravity_round32_jhora_pyjhora_fast_capture_pipeline_2026_06_26.md`

### J. 时区 / DST / 极地异常直接落地任务
输出：`antigravity_round32_timezone_dst_polar_direct_tasks_2026_06_26.md`

要求：
- 不要再泛讲风险
- 必须给出具体异常输入、预期防御、建议测试

### K. 传统技法真缺口再排序 Top 20
输出：`antigravity_round32_true_missing_techniques_rerank_top20_2026_06_26.md`

### L. 用户本地使用体验直接优化 Top 30
输出：`antigravity_round32_local_ux_direct_top30_2026_06_26.md`

### M. 可复用碎片第五轮排查
输出：`antigravity_round32_whole_machine_fragment_reuse_fifth_pass_2026_06_26.md`

### N. Codex Round 33 Top 200
输出：`antigravity_round32_codex_round33_top200_2026_06_26.md`

### O. 最终执行总板
输出：`antigravity_round32_final_execution_board_2026_06_26.md`

必须明确：
1. 今天最该写代码的前 20 项
2. 今天最该同步的前 10 项
3. 今天最该压给副手的前 20 项
4. 哪些必须等待人工 oracle
5. 哪些看起来热闹但应推迟

## 额外 4 份补充报告

副手还必须自选 4 份高影响补充报告，主题只能从以下范围选择：

- 本地离线模式 / API fallback
- 性能/内存/超大 JSON 压力
- 多语言/i18n/术语译名
- 真实用户的精度验证阻塞

## 状态定义

只有当报告真正能被 Codex “直接翻译成代码/同步命令/验证步骤”时，才能写：

`已成立`

否则只能写：

`部分成立` / `未成立` / `需要人工外部工具` / `license_blocked`
