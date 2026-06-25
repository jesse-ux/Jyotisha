# Antigravity AI 副手任务单 Round 26（2026-06-25）

## 任务目标

Round 25 已交付 18 份报告，但仍出现新的过强结论风险，例如：

- “Panchang 完全空白”可能不准确；当前项目已有 Panchanga range、Tithi/Nakshatra/Yoga end times、Rahu Kala/Yamaganda/Gulika、Choghadiya、Hora、CSV/ICS、Muhurta range solver 等能力。
- “直接把 VedAstro 查表转 Python”仍需要具体文件、license、字段、测试和不可复制边界。
- `accuracy` profile 当前未成立，Codex 正在 TDD 修复，副手需要黑盒验收，而不是重复旧失败。

本轮目标：**纠正 Round 25 过强判断、建立 Panchanga/Muhurta 真缺口清单、验收 accuracy profile、把下一批实现任务变成测试驱动票据**。

## 当前事实基线

必须重新验证，不要照搬 Round 25：

- 当前 repo 根计划文件存在：`task_plan.md`、`findings.md`、`progress.md`。
- 最新地毯式扫描文档：`docs/research/whole_machine_fragment_sweep_round25_2026_06_25.md`。
- Round 25 已有 18 份报告，但尚未归档提交。
- 本地 branch 可能仍 ahead 1；SSH 22 push 可能超时，远端 HTTPS refs 需重新查。
- `run_quality_gate.py --profile accuracy` 目前可能正在由 Codex 实现，副手必须跑最新状态。
- Panchanga/Muhurta 相关能力已存在，不能再粗暴说“完全空白”；应区分“已有计算/API/UI/导出”与“缺商业级日历体验/外部对标/节日权威表”。

## 工作量要求

本轮至少产出 **20 份 round26 报告**，全部写入 `docs/research/`，文件名必须含 `antigravity_round26_*_2026_06_25.md`。

每份报告必须包含：

- 至少 20 个检查点。
- 至少 8 条可复制命令、检索 token、URL、文件路径或代码位置。
- 至少 3 条 Codex 可直接实现的任务，必须含文件路径、测试、验收。
- 至少 2 条副手下一轮可继续做的任务。
- 至少 1 条需要人工 JHora/AstroSage/网页截图的任务。
- 状态必须标为：`已成立`、`部分成立`、`未成立`、`误判已纠正`、`需要人工外部工具`。
- 所有开源复用建议必须带 license；只有 MIT/Apache-2.0/BSD/ISC/CC0 可列为可复制候选。

## 严格边界

禁止：

- 不要修改 `scripts/`、`tests/`、`jyotish-app/`、`README.md`、`references/` 实现文件。
- 不要提交、推送、重置、删除、移动、覆盖文件。
- 不要读取或传播 token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串。
- 不要把用户私人 PDF/Obsidian 完整解盘/Downloads 原文提交或摘录。
- 不要把本地 baseline、模板值、空目标字段或副手推测写成 `external_verified`。
- 不要复制 GPL/AGPL/LGPL/闭源代码。

允许：

- 只能新增 `docs/research/*round26*2026_06_25.md` 报告文件。
- 可以运行只读测试、grep、build、quality gate。
- 可以联网检索公开项目、公开 docs、公开 license。
- 可以读取 `task_plan.md`、`findings.md`、`progress.md`、Round 25 报告和地毯式扫描文档。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 18
git ls-remote https://github.com/732642856/yinduzhanxing.git 'refs/heads/*' 'refs/tags/*' | sort
python3 scripts/local_accuracy_report.py --format json
python3 scripts/local_accuracy_report.py --format markdown
python3 scripts/run_quality_gate.py --profile accuracy
python3 -m pytest -q tests/test_frontend_productization.py::test_quality_gate_declares_fast_browser_release_profiles tests/test_frontend_productization.py::test_accuracy_quality_gate_runs_local_accuracy_report_without_frontend_click
rg -n "panchanga|Panchanga|panchang|Tithi|Nakshatra|Rahu Kala|Yamaganda|Gulika|Choghadiya|Hora|muhurta_range|range_search" scripts jyotish-app tests README.md task_plan.md findings.md progress.md
rg -n "def .*panch|panchanga_range|muhurta_range_search|/api/panchanga|/api/muhurta" scripts tests jyotish-app
python3 -m pytest -q tests/test_muhurta.py tests/test_api_server_security.py::test_panchanga_range_endpoint_returns_calendar_rows tests/test_api_server_security.py::test_muhurta_endpoint_returns_date_range_solver
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from ashtakoot import calculate_ashtakoot
for pair in [(0,0),(0,60),(0,160),(45,125),(180,300)]:
    r = calculate_ashtakoot(*pair)
    print(pair, r['total_score'], r['scores'])
PY
npm run build --prefix jyotish-app
git diff --check
```

如果某条命令失败，记录完整失败摘要，不要用旧结论替代。

## 工作包 A：Round 25 Panchang “完全空白”纠错

输出：`docs/research/antigravity_round26_panchang_round25_claim_correction_2026_06_25.md`

必须回答：

1. “Panchang 完全空白”是否成立。
2. 当前已有哪些 Panchanga API。
3. 当前已有哪些 Muhurta solver。
4. 当前前端是否显示 Panchanga/Muhurta。
5. 当前 CSV/ICS 是否已有。
6. 当前节日/vrata 是否只是 candidate。
7. 当前商业级缺口是什么。
8. 当前外部 oracle 缺口是什么。
9. 哪些 Round 25 文件需要带“结论存疑”阅读。
10. Codex 应该先补什么。
11. 副手下一轮该查什么。
12. 人工网页截图该采什么。
13. 文件证据。
14. 命令证据。
15. 测试证据。
16. UI 证据。
17. README 证据。
18. 风险。
19. 最终判定。
20. Top 10 修复票据。

## 工作包 B：accuracy profile 修复后黑盒验收

输出：`docs/research/antigravity_round26_accuracy_profile_postfix_blackbox_2026_06_25.md`

检查最新代码是否已实现 `--profile accuracy`，并给出失败/通过证据。

## 工作包 C：accuracy profile GitHub Actions 具体 YAML 方案

输出：`docs/research/antigravity_round26_accuracy_github_actions_yaml_plan_2026_06_25.md`

给出不直接修改代码的 workflow 草案和触发条件。

## 工作包 D：Round 25 报告归档前质量复核

输出：`docs/research/antigravity_round26_round25_archive_quality_audit_2026_06_25.md`

检查 18 份 Round 25 是否空文件、是否敏感、是否过强结论、是否值得提交。

## 工作包 E：Git 远端同步替代路径

输出：`docs/research/antigravity_round26_git_remote_sync_fallback_plan_2026_06_25.md`

围绕 SSH 22 超时设计 SSH-443/HTTPS/fetch/update-ref 方案，只写计划，不执行。

## 工作包 F：Panchanga 商业级日历缺口 Top 50

输出：`docs/research/antigravity_round26_panchanga_commercial_gap_top50_2026_06_25.md`

对标 AstroSage/Prokerala/Drik Panchang/JHora/VedAstro。

## 工作包 G：Muhurta range solver 外部对标

输出：`docs/research/antigravity_round26_muhurta_range_solver_benchmark_plan_2026_06_25.md`

设计外部截图/网页对标样本。

## 工作包 H：Ashtakoot VedAstro 查表迁移最小安全方案

输出：`docs/research/antigravity_round26_ashtakoot_vedastro_table_migration_safe_plan_2026_06_25.md`

必须列 license、具体文件、可复制范围、测试、回滚策略。

## 工作包 I：Ashtakoot oracle 5/5 人工采样 SOP

输出：`docs/research/antigravity_round26_ashtakoot_oracle_5_packet_sop_2026_06_25.md`

必须能直接交给人工执行。

## 工作包 J：Shadbala validator total/unit 二期实现票据

输出：`docs/research/antigravity_round26_shadbala_validator_phase2_tickets_2026_06_25.md`

拆出测试名、schema、字段、容差。

## 工作包 K：Kuja enum validator 实现票据

输出：`docs/research/antigravity_round26_kuja_enum_validator_tickets_2026_06_25.md`

拆出 enum、错误码、validator 和 API/UI 影响。

## 工作包 L：Prompt Pack 解盘安全护栏测试票据

输出：`docs/research/antigravity_round26_prompt_pack_guardrail_test_tickets_2026_06_25.md`

把“不铁口直断/不夸大准确率”转成测试。

## 工作包 M：前端隐藏高级技能按 ROI 排序

输出：`docs/research/antigravity_round26_frontend_hidden_skills_roi_rank_2026_06_25.md`

基于 Round 25 Top 50 重新排序，必须排除已可见功能。

## 工作包 N：API 未暴露技能按 ROI 排序

输出：`docs/research/antigravity_round26_api_missing_skills_roi_rank_2026_06_25.md`

必须排除已经有 `/api/*` 的能力。

## 工作包 O：CLI 普通用户体验修复票据

输出：`docs/research/antigravity_round26_cli_user_experience_fix_tickets_2026_06_25.md`

普通用户本机命令入口。

## 工作包 P：全机碎片扫描后续差距

输出：`docs/research/antigravity_round26_whole_machine_sweep_followup_gaps_2026_06_25.md`

基于 `whole_machine_fragment_sweep_round25`，列还需要读取的具体文件和原因。

## 工作包 Q：开源复用候选许可证二次确认

输出：`docs/research/antigravity_round26_open_source_license_second_pass_2026_06_25.md`

至少 25 个项目/文件，记录 license。

## 工作包 R：真实准确率用户说明草案

输出：`docs/research/antigravity_round26_user_accuracy_explainer_draft_2026_06_25.md`

写给普通用户，不要技术堆砌。

## 工作包 S：Codex Round 27 立即实现 Top 40

输出：`docs/research/antigravity_round26_codex_round27_top40_2026_06_25.md`

每项含文件、测试、验收、风险、是否需要人工。

## 工作包 T：最终总报告与自检

输出：`docs/research/antigravity_round26_final_summary_and_self_audit_2026_06_25.md`

必须回答：

1. Round 25 哪些结论被纠正。
2. accuracy profile 是否成立。
3. Panchanga/Muhurta 真实完成度。
4. Ashtakoot 下一步是否应重写或先 oracle。
5. Git 远端同步如何处理。
6. 当前必须由 Codex 做的前 20 件事。
7. 当前必须由副手继续做的前 20 件事。
8. 当前必须由人工 JHora/AstroSage 做的前 10 件事。

## 交付回复格式

最后回复必须列出：

- 20 份文件列表。
- 被纠正的 Round 25 误判。
- accuracy profile 结果。
- Panchanga/Muhurta 真实状态。
- 给 Codex 的前 20 个任务。
- 给副手 Round 27 的前 20 个任务。
- 需要人工外部工具的前 10 个任务。
