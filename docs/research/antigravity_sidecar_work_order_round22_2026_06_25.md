# Antigravity AI 副手任务单 Round 22（2026-06-25）

## 任务目标

本轮继续把高体量、低耦合、可并行的研究/审计交给副手。请注意：Round 21 报告中的两条旧建议已经被 Codex 执行或部分执行，不要再重复旧结论。

本轮重点是：复核双段 commit 是否已真正封存 Round 16-21 资产；复核 Ashtakoot validator 范围校验是否已落地；深挖 MIT 可复制的 Ashtakoot 36 分常量来源；继续推动 JHora/PyJHora 第一条真实证据；设计 Shadbala 总分二期、AI Prompt Pack Ashtakoot progress 和下一轮实现计划。

你只做只读复核、联网对标、报告和下一轮任务拆解；不要修改核心实现。

## 当前事实基线

必须以当前工作树重新验证，不要照抄 Round 21：

- Codex 已完成第一段产品提交：`feat: add oracle evidence safeguards`。
- Codex 已完成第二段研究资产提交：`docs(research): archive antigravity sidecar rounds`。
- `scripts/oracle_evidence_validator.py` 已包含 Ashtakoot 36 分制范围校验、8 Kuta 分项范围校验和 `ashtakoot_score_sum_mismatch`。
- `references/oracle/ashtakoot_oracle_cases.json` 已存在 5 条 draft cases。
- Dasha/Shadbala 真实 `external_verified` 仍为 0/5，不能伪造。
- 第一条 JHora/PyJHora 外部截图/stdout 仍等待人工工具。
- 本轮任务单文件为 `docs/research/antigravity_sidecar_work_order_round22_2026_06_25.md`。

## 工作量要求

本轮至少产出 20 份 `round22` 报告文件。每份报告必须包含：

- 至少 12 个检查点。
- 至少 3 条可复制命令、检索 token、URL 或代码位置。
- 至少 1 个 Codex 可直接改的文件建议。
- 状态必须标为 `已成立`、`部分成立`、`未成立`、`需要人工外部工具`。
- 发现旧结论过期时必须写“旧结论已过期”，并给出当前证据。
- 开源复用建议必须带 license；只有 MIT/Apache-2.0/BSD/ISC/CC0 进入“可复制候选”，GPL/AGPL/LGPL/闭源只能做行为参考。
- 最终总报告必须输出 Top 50 ROI 任务，并拆成：
  - Codex 可立即做
  - 副手继续可做
  - 必须等人工外部工具
  - 必须等用户决策/凭证

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录、传播 token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串或远程凭证。
- 不要打开、摘录或传播用户私人完整星盘报告、PDF 原件、出生资料正文。
- 不要修改 `scripts/`、`jyotish-app/`、`tests/`、`README.md`、`references/oracle/` 的实现内容。
- 不要把本仓库输出、`template_only`、`local_baseline` 或空目标字段标成 `external_verified`。
- 不要复制 JHora、PyJHora、AGPL/GPL/LGPL/闭源项目的实现代码、公式常量或内部表格。
- 不要用“绝对可信”“世界第一”“完全校准”等话术。

允许事项：

- 只能新增 `docs/research/*round22*2026_06_25.md` 报告文件。
- 可以读取 README、SKILL、progress、task_plan、Round 16-21 报告和本任务单。
- 可以读取 `scripts/ashtakoot.py`、`scripts/synastry.py`、`scripts/jyotish_engine.py`、`scripts/jyotish_api_server.py`、`scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`tests/**`、`jyotish-app/**`、`references/oracle/**`。
- 可以运行只读命令：`git status`、`git log`、`git show --stat`、`rg`、`pytest`、`npm run build --prefix jyotish-app`、`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic`。
- 可以联网检索公开开源项目、公开文档、公开产品页面；只记录 URL、license、能力点和差距，不抓取私人数据。

## 必跑命令

### 1. Git 与提交封存复核

```bash
git status --short --branch
git log --oneline --decorate -n 12
git show --stat --oneline HEAD~1
git show --stat --oneline HEAD
git status --short | wc -l
```

### 2. Ashtakoot validator 事实复核

```bash
rg -n "ASHTAKOOT_SCORE_RANGES|ASHTAKOOT_COMPONENT_FIELDS|invalid_ashtakoot_score_range|ashtakoot_score_sum_mismatch|target.total_score|target.nadi" \
  scripts/oracle_evidence_validator.py tests/test_oracle_evidence_validator.py
```

### 3. Oracle queue 复核

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/ashtakoot_oracle_cases.json \
  --format json > /tmp/jyotish_ashtakoot_queue_round22.json

python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_dasha_shadbala_queue_round22.json

python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_dasha_shadbala_queue_round22.json
```

### 4. 目标测试

```bash
python3 -m pytest -q \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_ashtakoot.py \
  tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated \
  tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards \
  tests/test_cli_smoke.py::test_full_reading_reports_ayanamsa_metadata_and_ai_prompt_pack
```

### 5. 构建与质量门

```bash
npm run build --prefix jyotish-app
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
git diff --check
```

若失败，报告失败测试名、断言、最小复现、真实风险等级和最小修复文件。

## 工作包 A：双段 commit 封存复核

输出：`docs/research/antigravity_round22_git_commit_blackbox_2026_06_25.md`

至少检查：

1. `feat: add oracle evidence safeguards` 是否存在。
2. `docs(research): archive antigravity sidecar rounds` 是否存在。
3. 第一 commit 是否包含产品/validator/oracle 文件。
4. 第二 commit 是否只包含研究报告和 work orders。
5. 是否还有 Round 16-21 报告处于 untracked。
6. 是否还有 oracle template 或 artifact policy untracked。
7. 是否有工作树残留。
8. 是否需要 push。
9. 是否需要 PR 更新。
10. 是否存在大文件风险。
11. 是否存在秘密泄漏风险。
12. 下一步 Git 建议。

## 工作包 B：Ashtakoot validator 修复后复核

输出：`docs/research/antigravity_round22_ashtakoot_validator_postfix_2026_06_25.md`

至少检查：

1. 是否定义 `ASHTAKOOT_SCORE_RANGES`。
2. `target.total_score` 是否限制 0-36。
3. `target.varna` 是否限制 0-1。
4. `target.vashya` 是否限制 0-2。
5. `target.tara` 是否限制 0-3。
6. `target.yoni` 是否限制 0-4。
7. `target.graha_maitri` 是否限制 0-5。
8. `target.gana` 是否限制 0-6。
9. `target.bhakoot` 是否限制 0-7。
10. `target.nadi` 是否限制 0-8。
11. 分项求和是否约等于 total。
12. bool/字符串/负数/超大值是否拒绝。
13. 仍缺什么，例如 `kuja_status` 枚举。

## 工作包 C：Kuja status 枚举与 Manglik 叠加设计

输出：`docs/research/antigravity_round22_kuja_status_enum_design_2026_06_25.md`

至少设计：

1. `kuja_status` 允许值。
2. 是否区分 `no_dosha`、`mild_dosha`、`strong_dosha`、`cancelled_dosha`。
3. 是否需要双方各自 Kuja status。
4. 是否进入 36 分总分。
5. 是否作为 penalty/flag 独立存在。
6. JHora/AstroSage/VedAstro 是否输出该项。
7. validator 错误码。
8. UI 展示。
9. tests。
10. 与现有 `mangal_dosha` 模块关系。
11. 是否等待外部 oracle。
12. 最小实现建议。

## 工作包 D：VedAstro Ashtakoot 常量深挖

输出：`docs/research/antigravity_round22_vedastro_ashtakoot_constants_deep_dive_2026_06_25.md`

联网检索并记录：

1. 仓库 URL。
2. license 文件 URL。
3. 目标代码路径。
4. 36 分或 Kuta 方法名。
5. Varna 常量。
6. Vashya 常量。
7. Tara 计算。
8. Yoni 常量。
9. Graha Maitri 常量。
10. Gana 常量。
11. Bhakoot 常量。
12. Nadi 常量。
13. Kuja/Manglik 逻辑。
14. 是否依赖其它类。
15. C# 到 Python 的最小移植计划。
16. attribution 文案。
17. 是否需要直接引入依赖。
18. 是否存在 license 冲突。

## 工作包 E：RaviKarrii MIT Java 常量深挖

输出：`docs/research/antigravity_round22_ravikarrii_constants_deep_dive_2026_06_25.md`

至少检查：

1. license。
2. Java package 结构。
3. 输入字段。
4. 输出字段。
5. 8 Kuta 常量。
6. 总分计算。
7. Nakshatra 映射。
8. Rashi 映射。
9. 测试样本。
10. API 示例。
11. 是否可复制。
12. 与 VedAstro 差异。
13. 最小可移植文件。
14. 风险等级。

## 工作包 F：不要复制清单复核

输出：`docs/research/antigravity_round22_do_not_copy_license_blacklist_2026_06_25.md`

至少列出 15 个不可复制或高风险来源：

- PyJHora
- pyhora2
- AstroSage
- JHora
- Maitreya
- Prokerala
- Hora Prakash
- 各类无 license GitHub 项目

每项说明为什么不能复制、可否黑盒对照、可否引用 URL、是否可用于人工采样。

## 工作包 G：Ashtakoot constants Python 数据结构设计

输出：`docs/research/antigravity_round22_ashtakoot_constants_python_schema_2026_06_25.md`

设计 `scripts/ashtakoot_constants.py`：

1. 文件职责。
2. 常量命名。
3. Nakshatra/Rashi 枚举。
4. 8 Kuta 表结构。
5. 源项目 attribution。
6. 是否需要 provenance 字段。
7. 测试 helper。
8. 不引入运行时依赖。
9. 与 `scripts/ashtakoot.py` 接口。
10. JSON vs Python dict 取舍。
11. 边界 case。
12. Codex 最小实现步骤。

## 工作包 H：Ashtakoot 已有算法与常量表接入差距

输出：`docs/research/antigravity_round22_ashtakoot_current_algorithm_gap_2026_06_25.md`

至少检查：

1. `scripts/ashtakoot.py` 当前输入。
2. 当前输出。
3. 当前分项是否硬编码。
4. 哪些函数需要替换。
5. 哪些测试已经覆盖。
6. 哪些测试是假覆盖。
7. 是否与 `/api/synastry` 使用同一实现。
8. 前端显示字段。
9. 会不会破坏旧用户流程。
10. 最小补丁文件。
11. TDD 红灯测试建议。
12. 是否需要 fixtures。

## 工作包 I：AI Prompt Pack 增加 Ashtakoot oracle progress 设计

输出：`docs/research/antigravity_round22_ai_prompt_ashtakoot_progress_design_2026_06_25.md`

至少设计：

1. 当前 `oracle_progress` 结构。
2. 是否新增 `ashtakoot_oracle_progress`。
3. 是否合并为 scopes 数组。
4. CLI 字段。
5. API 字段。
6. 前端 fallback 字段。
7. retrieval tag。
8. token 成本。
9. 用户边界文案。
10. tests。
11. Trust Center 显示。
12. 最小实现。

## 工作包 J：Shadbala 总分/单位二期复核

输出：`docs/research/antigravity_round22_shadbala_total_unit_validator_design_2026_06_25.md`

至少设计：

1. `target.shadbala_totals` schema。
2. `target.shadbala_unit` schema。
3. Rupa/Virupa 选择。
4. component sum vs total。
5. 每分项合理上限。
6. 每总分合理上限。
7. 容差。
8. JHora 截图如何读。
9. validator 错误码。
10. tests。
11. 是否阻塞第一条 1/5。
12. 最小实现。

## 工作包 K：Trust Center 0/5 到多 oracle 进度 UX

输出：`docs/research/antigravity_round22_trust_center_multi_oracle_progress_ux_2026_06_25.md`

至少覆盖：

1. Dasha/Shadbala 0/5。
2. Ashtakoot 0/5。
3. 用户会不会混淆。
4. 如何展示“可采集但不能调参”。
5. 如何展示“已验证但未满 5/5”。
6. 移动端布局。
7. 进度条颜色。
8. 错误列表。
9. 下载模板。
10. 打码提醒。
11. JHora 指南入口。
12. Ashtakoot 指南入口。

## 工作包 L：JHora 1/5 破冰执行外包包

输出：`docs/research/antigravity_round22_jhora_1_of_5_operator_packet_2026_06_25.md`

写成可以直接交给人的 checklist：

1. 需要什么电脑。
2. 下载/打开 JHora。
3. Steve Jobs 参数。
4. Lahiri。
5. true node。
6. Vimshottari 起点截图。
7. Shadbala 七曜六分量截图。
8. 打码示例。
9. 文件命名。
10. JSON 填写。
11. validator 命令。
12. 成功判据。
13. 失败重采。
14. 不得提交 PDF 原件。
15. 不得提交私人全名。

## 工作包 M：Ashtakoot 外部样本采集教程草案

输出：`docs/research/antigravity_round22_ashtakoot_capture_guide_draft_2026_06_25.md`

至少设计：

1. 5 个样本怎么填。
2. 外部来源优先级。
3. VedAstro API 采样。
4. AstroSage 页面采样。
5. JHora 合婚页面采样。
6. 截图命名。
7. 目标字段填写。
8. Kuja status 取值。
9. 隐私。
10. validator。
11. 0/5 到 1/5。
12. 不调参边界。

## 工作包 N：Release hygiene 与远端 push 风险

输出：`docs/research/antigravity_round22_push_readiness_audit_2026_06_25.md`

至少检查：

1. 当前分支 ahead 数。
2. 是否有未提交文件。
3. 是否有未跟踪报告。
4. 是否有大文件。
5. 是否有私人 artifact。
6. 是否有密钥。
7. quick gate。
8. build。
9. 是否建议 push。
10. 443 SSH fallback。
11. PR #6 是否需要更新。
12. 推送后核对命令。

## 工作包 O：同品类缺口 Top 50 重新排名

输出：`docs/research/antigravity_round22_competitor_gap_top50_2026_06_25.md`

必须重新排名，不要照抄旧报告。至少覆盖：

1. Ashtakoot 36 分。
2. Manglik/Kuja。
3. Shadbala external oracle。
4. Dasha external oracle。
5. Muhurta solver。
6. KP Horary。
7. Jaimini。
8. Tajika。
9. Ashtakavarga。
10. Report PDF。
11. API。
12. AI Prompt Pack。
13. PWA/Desktop shell。
14. 多语言。
15. 数据隐私。

## 工作包 P：Playwright/E2E 伪代码任务拆解

输出：`docs/research/antigravity_round22_playwright_e2e_task_breakdown_2026_06_25.md`

至少拆 20 条真实浏览器流程，覆盖 Trust Center、Oracle Evidence Intake、Ashtakoot 合盘、导入 evidence JSON、错误提示和移动端。

## 工作包 Q：Round 23 副手任务建议

输出：`docs/research/antigravity_round22_round23_sidecar_recommendations_2026_06_25.md`

至少给 25 条下一轮可并行任务，要求每条包含：

- 任务目标
- 读取文件
- 运行命令
- 输出报告文件名
- 不可做事项
- Codex 可消费结论

## 工作包 R：Codex Round 23 执行计划

输出：`docs/research/antigravity_round22_codex_round23_execution_plan_2026_06_25.md`

必须形成可执行计划：

1. 已完成项纠偏。
2. Top 10 下一步。
3. 每项文件。
4. 每项测试。
5. 是否联网。
6. 是否人工。
7. 是否需要用户确认。
8. 最小实现路径。
9. 不做事项。
10. 验收命令。
11. commit 拆分。
12. push 建议。

## 工作包 S：隐私/密钥二次扫描报告

输出：`docs/research/antigravity_round22_privacy_secret_rescan_2026_06_25.md`

至少检查：

1. `docs/research` 是否有真实 token。
2. `references/oracle/artifacts` 是否只有 `.gitkeep` 和 README。
3. `evidence_packet_templates` 是否无私人信息。
4. `.gitignore` 是否包含本地输出。
5. 是否有图片/PDF 被新增。
6. 是否有完整出生报告。
7. 是否有浏览器 scratch。
8. 是否有 API key。
9. 是否有 SSH key。
10. 是否有 cookie。
11. 是否可 push。
12. 最小修复建议。

## 工作包 T：总报告

输出：`docs/research/antigravity_round22_final_summary_and_round23_recommendations_2026_06_25.md`

必须汇总：

1. 本轮新增报告列表。
2. 每个工作包一句话结论。
3. 旧结论纠偏表。
4. P0/P1/P2 bug 表。
5. 可复制开源 Top 10。
6. 只能参考 Top 10。
7. 必须等待人工外部工具事项。
8. Codex 可立即做 Top 50。
9. 副手继续可做 Top 50。
10. Git/push 建议。
11. 生产调参是否允许。
12. Round 23 任务单建议。
