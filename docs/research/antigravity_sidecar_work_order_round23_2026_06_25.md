# Antigravity AI 副手任务单 Round 23（2026-06-25）

## 任务目标

本轮继续把高体量、低耦合、可并行的研究和黑盒复核交给副手。请注意：Round 22 回执中的两条结论已过期或不准确：

- “还需 push 上云”已过期：Round 16-22 work order 与前两段 commit 已经推送到远端。
- “`ashtakoot.py` 仍把 Varna/Tara 硬编码为 0”不符合当前源码。当前真实问题是：`/api/synastry` 之前调用了简化版 `scripts/synastry.py`，而 Codex 已开始切到完整 `scripts/ashtakoot.py::calculate_ashtakoot`。

本轮重点：复核 API 已切完整 Ashtakoot 引擎、验证前端/导出兼容字段是否仍可用、评估是否保留/删除简化 `synastry.py`、继续深挖 MIT 常量来源、推动 Round 22 报告入库与下一轮实现计划。

你只做只读复核、联网对标、报告和下一轮任务拆解；不要修改核心实现。

## 当前事实基线

必须重新验证：

- `scripts/jyotish_api_server.py::_compute_synastry` 已改为调用 `ashtakoot.calculate_ashtakoot`。
- API 返回中应保留旧字段别名：`is_approved`、`assessment`、`male`、`female`。
- `tests/test_api_server_security.py` 新增 `test_synastry_api_uses_full_ashtakoot_engine`。
- 聚焦测试 `tests/test_api_server_security.py ... tests/test_ashtakoot.py` 已经通过 50 项。
- 20 份 Round 22 报告仍需纳入 Git。
- Dasha/Shadbala 第一条真实 JHora/PyJHora `external_verified` 仍等待人工。

## 工作量要求

本轮至少产出 18 份 `round23` 报告文件。每份报告必须包含：

- 至少 12 个检查点。
- 至少 3 条可复制命令、检索 token、URL 或代码位置。
- 至少 1 个 Codex 可直接改的文件建议。
- 状态必须标为 `已成立`、`部分成立`、`未成立`、`需要人工外部工具`。
- 发现旧结论过期时必须写“旧结论已过期”，并给出当前证据。
- 开源复用建议必须带 license；只有 MIT/Apache-2.0/BSD/ISC/CC0 进入“可复制候选”，GPL/AGPL/LGPL/闭源只能做行为参考。
- 最终总报告必须输出 Top 50 ROI 任务，并拆成 Codex 可立即做、副手继续可做、必须等人工外部工具、必须等用户决策/凭证。

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录、传播 token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串或远程凭证。
- 不要打开、摘录或传播用户私人完整星盘报告、PDF 原件、出生资料正文。
- 不要修改 `scripts/`、`jyotish-app/`、`tests/`、`README.md`、`references/oracle/` 的实现内容。
- 不要把本仓库输出、`template_only`、`local_baseline` 或空目标字段标成 `external_verified`。
- 不要复制 JHora、PyJHora、AGPL/GPL/LGPL/闭源项目的实现代码、公式常量或内部表格。

允许事项：

- 只能新增 `docs/research/*round23*2026_06_25.md` 报告文件。
- 可以读取 Round 16-22 报告和本任务单。
- 可以读取 `scripts/ashtakoot.py`、`scripts/synastry.py`、`scripts/jyotish_api_server.py`、`tests/test_ashtakoot.py`、`tests/test_api_server_security.py`、`jyotish-app/**`、`references/oracle/**`。
- 可以运行只读命令：`git status`、`git log`、`git show --stat`、`rg`、`pytest`、`npm run build --prefix jyotish-app`、`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic`。
- 可以联网检索公开开源项目、公开文档、公开产品页面；只记录 URL、license、能力点和差距，不抓取私人数据。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 12
rg -n "def _compute_synastry|calculate_ashtakoot|is_approved|male_details|test_synastry_api_uses_full_ashtakoot_engine" \
  scripts/jyotish_api_server.py tests/test_api_server_security.py scripts/ashtakoot.py scripts/synastry.py
python3 -m pytest -q \
  tests/test_api_server_security.py::test_synastry_rejects_non_numeric_moon_degree \
  tests/test_api_server_security.py::test_synastry_normalizes_360_degree_boundary \
  tests/test_api_server_security.py::test_synastry_api_uses_full_ashtakoot_engine \
  tests/test_ashtakoot.py
npm run build --prefix jyotish-app
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
git diff --check
```

## 工作包 A：API 切换完整 Ashtakoot 引擎黑盒复核

输出：`docs/research/antigravity_round23_synastry_api_full_engine_blackbox_2026_06_25.md`

至少检查：

1. `_compute_synastry` 是否导入 `calculate_ashtakoot`。
2. 是否仍使用 `synastry.calc_ashtakoot`。
3. API result method 是否等于完整引擎。
4. scores 是否一致。
5. total_score 是否一致。
6. `is_match_approved` 是否存在。
7. 旧字段 `is_approved` 是否保留。
8. 旧字段 `male/female` 是否保留。
9. 360 度边界是否正常。
10. 非数字是否仍拒绝。
11. 前端是否消费旧字段。
12. 风险与下一步。

## 工作包 B：`scripts/synastry.py` 去留决策

输出：`docs/research/antigravity_round23_synastry_module_retirement_decision_2026_06_25.md`

至少检查：

1. 哪些代码仍 import `synastry.calc_ashtakoot`。
2. 哪些测试仍依赖 `synastry.py`。
3. `calc_synastry` 是否仍有兼容价值。
4. 是否应改为 wrapper 到 `ashtakoot.calculate_ashtakoot`。
5. 删除风险。
6. 保留风险。
7. 最小重构建议。
8. 测试建议。
9. API 影响。
10. 前端影响。
11. 文档影响。
12. 是否进入 Round 24。

## 工作包 C：前端合盘兼容字段复核

输出：`docs/research/antigravity_round23_frontend_synastry_compatibility_review_2026_06_25.md`

至少检查 `jyotish-app/main.js`：

1. `is_match_approved`。
2. `is_approved`。
3. `male_details/female_details`。
4. `male/female`。
5. `assessment`。
6. `additional_kutas`。
7. `BadConstellations`。
8. `kuja_dosha_*`。
9. 导出关系报告。
10. 保存关系案例。
11. 移动端显示。
12. E2E 缺口。

## 工作包 D：Round 22 报告入库策略复核

输出：`docs/research/antigravity_round23_round22_archive_strategy_2026_06_25.md`

至少检查：

1. 20 份 Round 22 报告是否存在。
2. 是否 untracked。
3. 是否有敏感信息。
4. 是否有大文件。
5. 是否应单独 commit。
6. commit message。
7. 是否需要 push。
8. 是否会影响 quick gate。
9. 是否与 Round 23 任务单同 commit。
10. 最小命令。
11. 风险。
12. 建议。

## 工作包 E：MIT 常量来源再核验

输出：`docs/research/antigravity_round23_mit_constants_source_recheck_2026_06_25.md`

联网复核至少 10 个来源，重点：

- VedAstro/VedAstro
- RaviKarrii/Marriage-Compatibility-Asthakoot
- flatlib
- panchanga
- dashaflow

记录 URL、license、可复制性、常量覆盖、代码质量、移植风险。

## 工作包 F：完整 Ashtakoot 引擎 provenance 设计

输出：`docs/research/antigravity_round23_ashtakoot_provenance_design_2026_06_25.md`

设计 API result 中加入：

1. source_project。
2. source_license。
3. algorithm_variant。
4. external_oracle_status。
5. constant_source。
6. calibration_status。
7. not_external_verified 边界。
8. tests。
9. UI 展示。
10. Prompt Pack 展示。
11. JSON 导出。
12. 最小实现。

## 工作包 G：Ashtakoot oracle progress 接入 Trust Center/Prompt Pack 计划

输出：`docs/research/antigravity_round23_ashtakoot_oracle_progress_integration_plan_2026_06_25.md`

至少设计 CLI、API、前端 fallback、Trust Center、AI Prompt Pack、测试和文案。

## 工作包 H：Kuja status enum 实现验收细化

输出：`docs/research/antigravity_round23_kuja_status_enum_acceptance_2026_06_25.md`

至少设计允许值、validator 错误码、UI 文案、测试样本、与 `calc_kuja_dosha` 的关系。

## 工作包 I：Shadbala total/unit 二期实现验收细化

输出：`docs/research/antigravity_round23_shadbala_total_unit_acceptance_2026_06_25.md`

至少设计 target schema、单位、范围、sum mismatch、测试样本和是否阻塞 1/5。

## 工作包 J：JHora 1/5 人工执行催办包

输出：`docs/research/antigravity_round23_jhora_1_of_5_operator_brief_2026_06_25.md`

写成能直接转给操作者的短版，不超过 80 行，但包含所有字段和验收命令。

## 工作包 K：Ashtakoot 外部采集包短版

输出：`docs/research/antigravity_round23_ashtakoot_external_capture_brief_2026_06_25.md`

写成能直接转给操作者的短版，覆盖 VedAstro/AstroSage/JHora 三源截图/API。

## 工作包 L：Playwright 合盘 E2E 最小可执行计划

输出：`docs/research/antigravity_round23_synastry_playwright_minimal_plan_2026_06_25.md`

至少给 12 条真实浏览器流程和具体 selector/token。

## 工作包 M：Push readiness 二次复核

输出：`docs/research/antigravity_round23_push_readiness_second_audit_2026_06_25.md`

检查当前分支 ahead、untracked、secret scan、quick gate、远端 HEAD。

## 工作包 N：Round 24 副手任务建议

输出：`docs/research/antigravity_round23_round24_sidecar_recommendations_2026_06_25.md`

至少给 30 条下一轮可并行任务。

## 工作包 O：Codex Round 24 执行计划

输出：`docs/research/antigravity_round23_codex_round24_execution_plan_2026_06_25.md`

给 Codex Top 15 实现计划，含文件、测试、是否联网、是否人工、验收命令。

## 工作包 P：总报告

输出：`docs/research/antigravity_round23_final_summary_and_round24_recommendations_2026_06_25.md`

必须汇总本轮新增报告、旧结论纠偏、P0/P1/P2、可复制开源、不可复制来源、人工事项、Codex Top 50、副手 Top 50、生产调参状态和 Round 24 建议。
