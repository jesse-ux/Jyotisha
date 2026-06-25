# Antigravity AI 副手任务单 Round 25（2026-06-25）

## 任务目标

Round 24 已收齐并归档，但其结论中存在需要复核的高风险点，特别是：

- “Ashtakoot 是假数据/全 0/瞎编”与当前 `scripts/ashtakoot.py` 的非零规则实现不完全一致。
- “直接抄 VedAstro 常量”需要 license、文件路径、具体函数、可复制范围和测试策略，不允许泛泛而谈。
- “全部技能未完成”需要拆成 UI/API/CLI/测试/外部 oracle 五层证据，不能只用主观判断。

本轮任务不是继续写宽泛报告，而是做 **证据级复核 + 可执行修复票据 + 副手下一轮自动化准备**。请把 Codex 的算力压力降到最低：你负责联网检索、只读审计、矩阵整理、反证检查和下一轮任务拆解。

## 当前主线事实

请重新验证：

- `scripts/local_accuracy_report.py` 已存在。
- `README.md` 已有本地准确率入口。
- Round 23 + Round 24 共 39 份报告已提交到本地 commit `bac3748`，push 可能受 GitHub SSH 网络延迟影响。
- `scripts/ashtakoot.py` 当前存在 `VASHYA_MATRIX`、`YONI_ENEMIES`、`GANA`、`NADI`、`FRIENDSHIP`、`calc_bhakoot` 等非零逻辑。
- `calculate_ashtakoot(0, 60)` 当前 total_score 约 27，不是全 0。
- 真实缺口是：Ashtakoot 外部 oracle 仍 0/5，不能声称与 JHora/AstroSage/VedAstro 完全一致。
- Codex 正在新增 `run_quality_gate.py --profile accuracy`，需要你黑盒验收。

## 工作量要求

本轮至少产出 **18 份 round25 报告**，全部写入 `docs/research/`，文件名必须含 `antigravity_round25_*_2026_06_25.md`。

每份报告必须包含：

- 至少 18 个检查点。
- 至少 6 条可复制命令、检索 token、URL、文件路径或代码位置。
- 至少 2 条“Codex 可直接实现”的任务。
- 至少 1 条“副手下一轮继续做”的任务。
- 至少 1 条“需要人工外部工具/JHora/AstroSage”的任务。
- 状态必须标为：`已成立`、`部分成立`、`未成立`、`误判已纠正`、`需要人工外部工具`。
- 任何开源复用建议必须带 license 证据；只有 MIT/Apache-2.0/BSD/ISC/CC0 可列入“可复制候选”。

## 严格边界

禁止：

- 不要修改 `scripts/`、`tests/`、`jyotish-app/`、`README.md`、`references/` 实现文件。
- 不要提交、推送、重置、删除、移动、覆盖文件。
- 不要读取或传播 token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串。
- 不要把本地 baseline、模板值、空目标字段或副手推测写成 `external_verified`。
- 不要复制 GPL/AGPL/LGPL/闭源项目代码。

允许：

- 只能新增 `docs/research/*round25*2026_06_25.md` 报告文件。
- 可以运行只读测试、grep、build、quality gate。
- 可以联网检索公开项目、公开 docs、公开 license。
- 可以引用本仓库源码位置和测试输出。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 16
python3 scripts/local_accuracy_report.py --format json
python3 scripts/local_accuracy_report.py --format markdown
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts')
from ashtakoot import calculate_ashtakoot
for pair in [(0,0),(0,60),(0,160),(45,125),(180,300)]:
    r = calculate_ashtakoot(*pair)
    print(pair, r['total_score'], r['scores'])
PY
python3 -m pytest -q tests/test_ashtakoot.py tests/test_api_server_security.py::test_synastry_api_uses_full_ashtakoot_engine
python3 -m pytest -q tests/test_frontend_productization.py::test_quality_gate_declares_fast_browser_release_profiles tests/test_frontend_productization.py::test_accuracy_quality_gate_runs_local_accuracy_report_without_frontend_click
python3 scripts/run_quality_gate.py --profile accuracy
npm run build --prefix jyotish-app
git diff --check
```

如果 `--profile accuracy` 还未实现，请明确标注为 `未成立`，并记录失败输出。

## 工作包 A：Round 24 Ashtakoot 误判纠正报告

输出：`docs/research/antigravity_round25_ashtakoot_round24_claim_correction_2026_06_25.md`

必须回答：

1. “Ashtakoot 全是 0”是否成立。
2. 哪些函数确实返回非零。
3. 哪些常量/矩阵确实存在。
4. 哪些地方仍不像商业/JHora 输出。
5. 外部 oracle 0/5 对可信度意味着什么。
6. 哪些 Round 24 文件需要被 Codex 以“报告结论存疑”对待。
7. 是否应该立刻重写 `ashtakoot.py`。
8. 是否应该先加 provenance 和 oracle progress。
9. 最小修复任务。
10. 测试任务。
11. UI 提示任务。
12. README 边界任务。
13. 外部采样任务。
14. license 风险。
15. 用户体验风险。
16. 下一轮计划。
17. 可复制命令。
18. 最终判定。

## 工作包 B：VedAstro MIT 可复制范围精确核验

输出：`docs/research/antigravity_round25_vedastro_mit_reuse_scope_2026_06_25.md`

联网检索并记录：

- 仓库 URL。
- LICENSE URL。
- 具体文件路径。
- 相关函数/类名。
- 是否 MIT。
- 是否包含 Ashtakoot 常量。
- 是否包含 Panchang/Tithi。
- 是否包含 Shadbala。
- C# 到 Python 迁移风险。
- 哪些可复制。
- 哪些只可参考。
- 至少 10 条源链接/检索记录。

## 工作包 C：Ashtakoot 外部 oracle 采集最短路径

输出：`docs/research/antigravity_round25_ashtakoot_oracle_shortest_path_2026_06_25.md`

必须设计 5 条可在今天完成的样本：

- 输入月亮度数。
- JHora/AstroSage/VedAstro 来源。
- 目标字段。
- 截图位置。
- JSON 填写路径。
- 验证命令。
- 失败处理。

## 工作包 D：accuracy profile 黑盒验收

输出：`docs/research/antigravity_round25_accuracy_profile_blackbox_2026_06_25.md`

检查：

1. argparse choices 是否含 `accuracy`。
2. `QUALITY_GATE_PROFILES` 是否含 accuracy。
3. 是否跑 `local_accuracy_report.py`。
4. 是否跳过前端 click。
5. 是否跳过 frontend runtime。
6. 是否跑 real cases。
7. 是否跑 Dasha audit。
8. 是否跑 oracle audit。
9. 是否跑 Yoga logic。
10. README 是否说明。
11. pytest 是否覆盖。
12. 命令是否可执行。
13. 运行时间。
14. 输出是否清楚。
15. 失败时 next_action。
16. 是否可用于用户准确率测试。
17. 是否适合 CI。
18. 下一步建议。

## 工作包 E：质量门禁 accuracy profile CI 接入计划

输出：`docs/research/antigravity_round25_accuracy_profile_ci_plan_2026_06_25.md`

设计 GitHub Actions/本地使用策略，不修改代码。

## 工作包 F：前端技能不可见 Top 50

输出：`docs/research/antigravity_round25_frontend_invisible_skills_top50_2026_06_25.md`

用文件 token 证明哪些技能已经有 CLI/API 但 UI 不可见。

## 工作包 G：API 未暴露技能 Top 50

输出：`docs/research/antigravity_round25_api_missing_skills_top50_2026_06_25.md`

用 registry、engine、server handler 对照。

## 工作包 H：CLI 用户体验阻塞 Top 50

输出：`docs/research/antigravity_round25_cli_usability_blockers_top50_2026_06_25.md`

重点普通用户本地能不能用。

## 工作包 I：Prompt Pack 解盘可信度修复票据

输出：`docs/research/antigravity_round25_prompt_pack_trust_fix_tickets_2026_06_25.md`

把“过度铁口直断”风险拆成 Codex 可改的测试和文案。

## 工作包 J：Panchang/Tithi/Muhurta 缺口实现优先级

输出：`docs/research/antigravity_round25_panchang_muhurta_gap_priority_2026_06_25.md`

对标商业应用日历功能。

## 工作包 K：Shadbala validator 二期验收

输出：`docs/research/antigravity_round25_shadbala_validator_phase2_acceptance_2026_06_25.md`

设计 total/unit/range/tolerance schema。

## 工作包 L：Kuja enum validator 验收

输出：`docs/research/antigravity_round25_kuja_enum_validator_acceptance_2026_06_25.md`

设计 enum、错误码、测试样本。

## 工作包 M：外部 oracle 1/5 破冰执行包 v2

输出：`docs/research/antigravity_round25_first_oracle_packet_v2_operator_brief_2026_06_25.md`

压缩到操作者 30 分钟可执行。

## 工作包 N：README 准确率章节重写建议

输出：`docs/research/antigravity_round25_readme_accuracy_section_rewrite_2026_06_25.md`

提出新段落和不应宣称的边界。

## 工作包 O：Round 25 Codex 立即实现 Top 30

输出：`docs/research/antigravity_round25_codex_immediate_top30_2026_06_25.md`

每项含文件、测试、验收、风险。

## 工作包 P：Round 26 副手任务建议

输出：`docs/research/antigravity_round25_sidecar_round26_recommendations_2026_06_25.md`

至少 30 项。

## 工作包 Q：最终总报告

输出：`docs/research/antigravity_round25_final_summary_2026_06_25.md`

必须回答：

1. Round 24 哪些结论被纠正。
2. 当前最该做的本地实现是什么。
3. 当前最该做的外部 oracle 是什么。
4. 当前哪些任务可以交给副手继续做。
5. 当前用户如何测试准确率。
6. 真实完成度。

## 工作包 R：副手自检

输出：`docs/research/antigravity_round25_self_audit_2026_06_25.md`

检查是否跑命令、是否误判、是否写够 18 份、是否含 license、是否无敏感信息。

## 交付回复格式

最后回复必须列出：

- 18+ 文件列表。
- 被纠正的 Round 24 误判。
- 当前 Ashtakoot 的真实状态。
- accuracy profile 是否成立。
- 给 Codex 的前 20 个可执行任务。
- 给副手 Round 26 的前 20 个任务。
- 需要人工 JHora/AstroSage 的前 10 个任务。
