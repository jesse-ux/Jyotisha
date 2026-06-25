# Antigravity AI 副手任务单 Round 14（2026-06-25）

## 任务目标

本轮继续优先“技法与准确率”，聚焦 Round 13 发现的最大断点：系统已经能下载空白 Evidence Packet，但还缺“上传填写后的 Evidence Packet 并本地判卷”的闭环。

请只做黑盒复核与报告，不修改核心实现。

需要确认：

1. Web/App 是否提供填写后 Evidence Packet 的导入入口。
2. 导入后是否能调用本地 validator，返回 `valid_packets`、`ready_for_calibration`、`production_tuning_allowed`、`problems`。
3. 本地输出、空字段、`status=draft` 是否仍被拦截。
4. 面向普通用户的红灯/绿灯文案是否足够明确，不把 `external_verified` 当成自动调参。
5. 下一步哪个技法最值得投入真实外部样本：Shadbala 六分量、Vimshottari Dasha 边界、Ashtakoot 合婚或 KP Sub Lord。

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 GitHub token、API key、浏览器登录态、cookie、SSH 私钥或系统钥匙串。
- 不要打开或摘录用户私人星盘完整报告正文。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/`、`README.md` 的实现内容。
- 不要把 `output_report.txt`、`results_extracted.md`、PDF 原件、Antigravity scratch 或私人出生资料纳入同步建议。
- 不要复制 JHora、PyJHora、AGPL/GPL 项目的实现代码、公式常量或内部数据表。
- 不要把 `template_only`、`local_baseline`、本仓库输出或空目标字段标成 `external_verified`。
- 不要使用“绝对可信”“世界第一”“完全校准”等过度准确率话术。

允许事项：

- 可以读取 `README.md`、`SKILL.md`、`progress.md`。
- 可以读取 `docs/research/*round13*`、本任务单和相关公开研究报告。
- 可以读取 `scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`scripts/jyotish_api_server.py`、`jyotish-app/main.js`、`api-bridge.js`、`style.css`、`tests/test_frontend_productization.py`、`tests/test_oracle_evidence_validator.py`，只做复核。
- 可以运行只读命令：`git status`、`git log`、`rg`、`python3 ... --format json`、`pytest`、`npm run build --prefix jyotish-app`。
- 只能新增 `docs/research/*round14*2026_06_25.md` 报告文件。

## 必跑命令

### 1. Git / 本地状态复核

```bash
git status --short --branch
git log --oneline --decorate -n 8
```

### 2. Evidence Packet 导入/判卷静态复核

```bash
rg -n "oracle-evidence-upload|oracle-import-packet|validateOracleEvidencePacket|validateOracleEvidence|/api/oracle_evidence|external_oracle_evidence_validation|valid_packets|ready_for_calibration|production_tuning_allowed|status_not_external_verified|local_engine_artifact_rejected" \
  jyotish-app/main.js \
  jyotish-app/api-bridge.js \
  scripts/jyotish_api_server.py \
  tests/test_frontend_productization.py \
  tests/test_oracle_evidence_validator.py
```

### 3. 防污染回归复验

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round14.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round14.json
```

```bash
python3 -B -m pytest \
  tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  -q
```

### 4. 用户端构建复核

```bash
npm run build --prefix jyotish-app
```

## 输出报告 A：Evidence Packet 导入判卷黑盒复核

输出文件：

- `docs/research/antigravity_round14_evidence_packet_validation_blackbox_2026_06_25.md`

固定小节：

1. 对标
2. 开源参考
3. Bug

必须判断：

- 用户是否能把填写后的 JSON 包导入。
- 是否能得到 validator 的结构化结果。
- 是否能清楚看到每个 `problems` 项。
- 是否仍会拦截本地输出、空字段和 `draft`。

## 输出报告 B：准确率闭环剩余断点

输出文件：

- `docs/research/antigravity_round14_accuracy_loop_remaining_gaps_2026_06_25.md`

请输出表格：

| 环节 | 当前状态 | 缺口 | 建议文件 | 验收标准 |
|---|---|---|---|---|

至少覆盖：

- Evidence Packet 下载
- Evidence Packet 上传
- Validator 判卷
- 外部截图/工件存档
- `references/oracle/dasha_shadbala_oracle_cases.json` 晋级
- 生产调参开关
- 用户端准确率披露

## 输出报告 C：真实外部样本采集 SOP

输出文件：

- `docs/research/antigravity_round14_external_sample_collection_sop_2026_06_25.md`

请写一份不触碰源码、不复制实现的黑盒 SOP：

1. JHora 手工录入样本。
2. 截图哪些页面。
3. 记录哪些字段。
4. 如何填写 Evidence Packet。
5. 如何运行 validator。
6. 什么条件下不能晋级 `external_verified`。

必须特别说明：

- PyJHora 只可作为黑盒命令输出来源，不能复制 AGPL 实现。
- JHora 只可作为手动截图/输出来源，不能逆向实现。
- VedAstro 可作为次级黄经校验，不适合作为唯一 Shadbala 绝对值真值。

## 输出报告 D：给 Codex 的 Round 15 任务建议

输出文件：

- `docs/research/antigravity_round14_codex_round15_recommendations_2026_06_25.md`

请给出 3-5 个可执行任务，并明确每个任务涉及的文件路径、测试命令和验收标准。

优先考虑：

1. 增加外部截图工件目录与命名规范。
2. 增加 Evidence Packet 导入后的本地存档和版本记录。
3. 补第一条真实 JHora external_verified 样本。
4. 将 Shadbala 六分量校验从“占位字段”升级到逐行完整性校验。
5. 把技法优先级矩阵同步到 README/Trust Center。

## 最终回报格式

请用中文输出：

1. 已创建的文件列表。
2. Evidence Packet 导入/判卷是否闭环。
3. 防污染规则是否仍有效。
4. 真实样本采集还缺什么。
5. Bug 表（P0/P1/P2，文件路径，行号或搜索 token，修复建议）。

结尾必须写：

> 下一步建议 Codex 优先……
