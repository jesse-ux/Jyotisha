# Antigravity AI 副手任务单 Round 8（2026-06-25）

## 角色边界

本轮继续作为外部审计、对标分析与黑盒复验副手。Codex 已修复一个关键晋级路径问题：当 `references/oracle/dasha_shadbala_oracle_cases.json` 中某个 template case 被人工填入外部目标值并升为 `external_verified` 时，`oracle_collection_queue.py` 必须保留该证据包状态、metadata 和目标值，而不能重新生成成 `draft`。

你本轮要复核两件事：

1. 外部证据包从 oracle JSON → collection queue → evidence validator 的晋级链路是否可执行。
2. 当前项目距离 VedAstro、PyJHora、JHora 这三类对标项目还差哪些“具体文件/功能/数据”。

禁止事项：

- 不要提交、重置、删除、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 token、API key、浏览器登录态、系统钥匙串或远端凭证。
- 不要复制 JHora/PyJHora/AGPL/GPL 项目的实现代码、公式常量或内部数据表。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/` 下的实现文件。
- 不要把 `template_only`、`local_baseline`、本仓库输出或空目标字段标成 `external_verified`。
- 不要建议为了单个样本调生产常数、Shadbala global scaling、Dasha 年长常数。
- 不要使用“绝对可信”“世界第一”“完全校准”这类过度产品话术。

允许事项：

- 可以读取 `scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`scripts/run_quality_gate.py`、`references/oracle/dasha_shadbala_oracle_cases.json`、`tests/test_oracle_collection_queue.py`、`tests/test_oracle_evidence_validator.py`、`tests/test_frontend_productization.py`、`README.md` 和 Round 7 报告。
- 可以运行只读验证命令。
- 可以在 `/tmp` 生成临时 oracle JSON、queue JSON、validator 日志。
- 可以联网检索 VedAstro、PyJHora、JHora 的公开资料；只记录产品/功能差距，不复制代码。
- 可以创建 `docs/research/*round8*2026_06_25.md` 报告。

## 必跑命令

请先运行当前主链路：

```bash
python3 -B -m pytest \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated \
  -q
```

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round8.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round8.json
```

再创建一个 `/tmp/round8_one_external_verified_oracle.json` 临时文件：复制 `references/oracle/dasha_shadbala_oracle_cases.json`，只把第一个 `template_cases[0]` 改成：

- `status: external_verified`
- `target.moon_sidereal_longitude_deg`: 任意非空数值，例如 `311.7897`
- `target.vimshottari_start_date`: `1986-05-18`
- `target.shadbala_components.Sun.sthana/dig/kala/chesta/naisargika/drik`: 任意非空数值
- `evidence_packet.status: external_verified`
- `evidence_packet.metadata.tool_name: JHora`
- `evidence_packet.metadata.source_artifact`: 指向一个外部截图路径字符串
- 其余 required metadata 填满

然后运行：

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file /tmp/round8_one_external_verified_oracle.json \
  --format json > /tmp/round8_one_external_verified_queue.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/round8_one_external_verified_queue.json
```

预期状态：

- 原始队列仍是 `total_tasks: 5`、`ready_for_calibration: 0`、`valid_packets: 0`。
- 临时 one-verified 队列应出现 `ready_for_calibration: 1`。
- 临时 validator 应出现 `valid_packets: 1`、`ready_for_calibration: 1`、`production_tuning_allowed: false`。
- 已验证的 packet 必须保留 `metadata.tool_name == JHora`，并且 `target_placeholders` 覆盖 `target_fields`。

## 对标任务 A：外部证据晋级链路黑盒复验

输出文件：

- `docs/research/antigravity_round8_external_evidence_promotion_blackbox_2026_06_25.md`

必须检查：

- `target_fields` 是否存在。
- `external_verified` packet 是否会被保留，而不是被降级回 `draft`。
- `target_placeholders` 是否覆盖 `target_fields`。
- 单个 packet valid 时，是否仍保持 `production_tuning_allowed: false`，避免单样本调参。

## 开源参考任务 B：VedAstro / PyJHora / JHora 差距矩阵

输出文件：

- `docs/research/antigravity_round8_global_gap_matrix_2026_06_25.md`

必须联网或使用公开资料交叉确认，并用中文输出表格：

| 对标对象 | 强项 | 我们当前对应文件/功能 | 仍缺什么 | 建议优先级 | 不可复制/许可证边界 |
|---|---|---|---|---|---|

至少覆盖：

- VedAstro：API 化、596+ calculation methods、Koota、Panchanga、AI/Chat/API product surface。
- PyJHora：大量 dhasa、chart、strength、match、prediction 模块；AGPL-3.0，不能复制实现。
- JHora：桌面专业软件、Shadbala/Dasha 截图级真值、传统设置项；闭源，只能人工截图/黑盒对齐。

必须落到本项目具体文件，例如：

- `references/oracle/dasha_shadbala_oracle_cases.json`
- `scripts/oracle_collection_queue.py`
- `scripts/oracle_evidence_validator.py`
- `scripts/shadbala.py`
- `scripts/dasha_calculator_enhanced.py`
- `jyotish-app/*`
- `SKILL.md`

## Bug 任务 C：普通用户可用性差距

输出文件：

- `docs/research/antigravity_round8_user_product_gap_audit_2026_06_25.md`

必须按 P0/P1/P2 表格输出：

| 严重程度 | 文件路径 | 行号 | 现象 | 用户影响 | 修复建议 |
|---|---|---:|---|---|---|

重点检查：

- 普通用户是否知道 Dasha/Shadbala 还在外部证据校准中。
- Web/App 是否能解释 `ready_for_calibration: 0`。
- Skill 是否会过度宣称准确率。
- JHora/PyJHora 外部真值采集是否仍需要人工步骤。
- 产品安装/运行路径是否离“一键普通用户使用”还有距离。

## 普通用户/产品任务 D：下一步路线图

输出文件：

- `docs/research/antigravity_round8_next_product_roadmap_2026_06_25.md`

必须分三章：

1. 对标
2. 开源参考
3. Bug

必须输出“下一步给 Codex 的可执行任务”，按优先级排列，建议包括：

- P1：完成 external_verified 导入器/校验器闭环。
- P1：采集至少 3 个 JHora/PyJHora/JHora screenshot 真值样本。
- P1：在网页/app Trust Center 暴露 Dasha/Shadbala calibration status。
- P2：补 VedAstro 风格 Koota/Panchanga/API docs 差距。
- P2：补一键 Docker/桌面壳普通用户启动路径。

## 最终回复格式

完成后在 Antigravity 聊天里回复：

1. 已创建哪些 `docs/research/*round8*2026_06_25.md` 文件。
2. external_verified 晋级链路是否通过黑盒复验。
3. 当前相对 VedAstro/PyJHora/JHora 的前三大差距。
4. P0/P1/P2 Bug 总表。
5. 下一步建议给 Codex 的可执行修复事项。

最终报告必须使用中文，章节固定为：

- 对标
- 开源参考
- Bug
