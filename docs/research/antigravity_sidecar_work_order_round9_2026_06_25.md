# Antigravity AI 副手任务单 Round 9（2026-06-25）

## 角色边界

本轮继续作为外部审计、黑盒复验与产品差距副手。Round 8 已确认 external_verified 晋级链路可用，也指出当前最大的普通用户风险是 Web/App 没有显式展示 Dasha/Shadbala 仍在外部校准队列中。

你本轮要做两件事：

1. 黑盒复核网页/app 与 Skill 是否已经或尚未向普通用户披露 Dasha/Shadbala calibration status。
2. 给 Codex 输出下一步可执行修复清单，重点围绕 Trust Center、Skill 文案和一键使用路径。

禁止事项：

- 不要提交、重置、删除、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 token、API key、浏览器登录态、系统钥匙串或远端凭证。
- 不要复制 JHora/PyJHora/AGPL/GPL 项目的实现代码、公式常量或内部数据表。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/` 下的实现文件。
- 不要把 `template_only`、`local_baseline`、本仓库输出或空目标字段标成 `external_verified`。
- 不要使用“绝对可信”“世界第一”“完全校准”等过度准确率话术。

允许事项：

- 可以读取 `README.md`、`SKILL.md`、`jyotish-app/index.html`、`jyotish-app/main.js`、`jyotish-app/style.css`、`jyotish-app/ai-chat.js`、`scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`references/oracle/dasha_shadbala_oracle_cases.json`、Round 8 报告。
- 可以运行只读验证命令。
- 可以创建 `docs/research/*round9*2026_06_25.md` 报告。
- 可以联网查询 VedAstro/JHora/PyJHora 的公开产品呈现方式，但只做产品差距分析，不复制代码。

## 必跑命令

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round9.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round9.json
```

```bash
python3 -B -m pytest \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated \
  -q
```

如果你能安全运行前端静态搜索，请执行：

```bash
grep -R "ready_for_calibration\|Dasha/Shadbala\|external_oracle_evidence_validation\|calibration" -n README.md SKILL.md jyotish-app | head -n 80
```

## 对标任务 A：普通用户校准透明度黑盒审计

输出文件：

- `docs/research/antigravity_round9_user_calibration_transparency_audit_2026_06_25.md`

必须检查：

- README 是否说明 `ready_for_calibration: 0`。
- SKILL 是否避免宣称 Dasha/Shadbala 已完全校准。
- Web/App 首屏或 Trust Center 是否展示 calibration status。
- AI Chat 是否会把 Dasha/Shadbala 外部校准状态纳入提示或安全边界。
- 当前用户能否区分“基础 D1/D9 高可信”和“Dasha/Shadbala 仍在外部证据采集中”。

## 开源参考任务 B：竞品透明度对比

输出文件：

- `docs/research/antigravity_round9_competitor_transparency_gap_2026_06_25.md`

必须用中文表格输出：

| 对标对象 | 透明度呈现 | 我们当前呈现 | 缺口 | 推荐修复 |
|---|---|---|---|---|

至少覆盖：

- VedAstro：API/文档/计算方法可见性。
- JHora：桌面软件中设置项、分量表、截图可核验。
- PyJHora：开源函数面广，但 AGPL 边界要求只能黑盒参考。

## Bug 任务 C：文件级 Bug 报告

输出文件：

- `docs/research/antigravity_round9_calibration_status_bug_report_2026_06_25.md`

必须按表格输出：

| 严重程度 | 文件路径 | 行号 | 现象 | 用户影响 | 修复建议 |
|---|---|---:|---|---|---|

严重度定义：

- P0：用户界面可能让普通用户误以为 Dasha/Shadbala 已完全外部校准。
- P1：Trust Center / Skill / AI Chat 缺少 `ready_for_calibration` 或 evidence validator 状态。
- P2：文案不够清楚、入口太深、命令过于开发者化。

## 产品任务 D：下一步修复方案

输出文件：

- `docs/research/antigravity_round9_next_fix_plan_2026_06_25.md`

必须分三章：

1. 对标
2. 开源参考
3. Bug

必须给 Codex 一个可执行修复顺序：

- 先在 `jyotish-app` Trust Center 增加 “Dasha/Shadbala Calibration Status”。
- 再让 `/api/capability_audit` 或静态前端读取/展示 oracle queue summary。
- 再同步 `SKILL.md` 与 AI Chat prompt boundary。
- 最后把 Docker/桌面壳一键启动作为普通用户交付优化。

## 最终回复格式

完成后在 Antigravity 聊天里回复：

1. 已创建哪些 `docs/research/*round9*2026_06_25.md` 文件。
2. 当前 Web/App/Skill 是否已充分披露 Dasha/Shadbala 校准状态。
3. P0/P1/P2 Bug 总表。
4. 下一步建议给 Codex 的可执行修复事项。

最终报告必须使用中文，章节固定为：

- 对标
- 开源参考
- Bug
