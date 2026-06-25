# Antigravity AI 副手任务单 Round 11（2026-06-25）

## 任务目标

本轮任务只做“修复后复核”和“下一批缺口排序”，不要改核心代码。

请重点确认 Codex 已完成的 Round 10 后续修复是否真正闭环：

1. GitHub 远端 `codex/release-hygiene-ci` 是否已经同步到 `56a86dd` 或更高提交。
2. Web/App 的 Trust Center 是否已经展示 `Dasha/Shadbala Calibration Status`。
3. AI Chat、API prompt bridge、`SKILL.md` 是否都强制说明：`ready_for_calibration: 0`，不得把大运起点或 Shadbala 绝对值说成已完成外部校准。
4. 本机碎片扫描后，是否仍有需要同步到主仓但遗漏的产品代码、测试或公开研究报告。
5. 按全球同类标杆重新排序：距离普通用户成品还差哪些最高优先级任务。

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

- 可以读取 `README.md`、`SKILL.md`、`task_plan.md`、`findings.md`、`progress.md`。
- 可以读取 `docs/research/*round10*`、本任务单和相关公开研究报告。
- 可以读取 `jyotish-app/main.js`、`jyotish-app/ai-chat.js`、`jyotish-app/api-bridge.js`、`jyotish-app/public/api-bridge.js`、`jyotish-app/style.css`、`tests/test_frontend_productization.py`，只做复核。
- 可以运行只读命令：`git status`、`git log`、`git ls-remote`、`rg`、`find`、`python3 ... --format json`、`pytest`、`npm run build --prefix jyotish-app`。
- 可以联网查询公开对标资料，但只做产品差距和许可证边界分析，不复制代码。
- 只能新增 `docs/research/*round11*2026_06_25.md` 报告文件。

## 必跑命令

### 1. Git / GitHub 同步复核

```bash
git status --short --branch
git log --oneline --decorate -n 8
```

```bash
GIT_SSH_COMMAND='ssh -p 443 -o IPQoS=none -o ConnectTimeout=30' \
git ls-remote ssh://git@ssh.github.com:443/732642856/yinduzhanxing.git \
  refs/heads/codex/release-hygiene-ci refs/heads/main
```

必须回答：

- 本地 HEAD 是什么 commit。
- 远端 `codex/release-hygiene-ci` 是什么 commit。
- 二者是否一致。
- 本地是否还有未提交/未推送的公开产品文件。

### 2. 校准透明度静态复核

```bash
rg -n "DASHA_SHADBALA_CALIBRATION_STATUS|Dasha/Shadbala Calibration Status|ready_for_calibration: 0|valid_packets: 0|production_tuning_allowed: false|external_oracle_evidence_validation|不得把大运起点或 Shadbala 绝对值说成已完成外部校准" \
  jyotish-app/main.js \
  jyotish-app/ai-chat.js \
  jyotish-app/api-bridge.js \
  jyotish-app/public/api-bridge.js \
  jyotish-app/style.css \
  SKILL.md \
  tests/test_frontend_productization.py
```

必须判断：

- Trust Center 面板是否存在。
- AI Chat 本地 fallback 与服务端 prompt 是否都注入边界。
- `public/api-bridge.js` 是否与源码 bridge 保持同步。
- `SKILL.md` 是否要求普通用户口径区分 D1/D9/SAV 高可信与 Dasha/Shadbala 外部校准中。

### 3. Oracle / evidence gate 复验

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round11.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round11.json
```

```bash
python3 -B -m pytest \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_frontend_productization.py::test_trust_center_and_ai_expose_dasha_shadbala_calibration_status \
  tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated \
  -q
```

### 4. 用户端构建复核

```bash
npm run build --prefix jyotish-app
```

### 5. 本机碎片复扫

只扫描文件名/路径，不读取私人报告正文：

```bash
for base in \
  /Users/wuyongnaren/Documents \
  /Users/wuyongnaren/Downloads \
  /Users/wuyongnaren/Desktop \
  /Users/wuyongnaren/Projects \
  /Users/wuyongnaren/WorkBuddy \
  /Users/wuyongnaren/.workbuddy \
  /Users/wuyongnaren/.codex \
  /Users/wuyongnaren/.gemini \
  /Users/wuyongnaren/engines-repo \
  /Users/wuyongnaren/文件仓库
do
  [ -e "$base" ] || continue
  echo "### $base"
  find "$base" -type d \( \
      -name node_modules -o -name .cache -o -name Library -o -name Applications \
      -o -name .Trash -o -name .npm -o -name .cargo -o -name .rustup \
      -o -name .pyenv -o -name .venv -o -name venv -o -name __pycache__ \
      -o -name .pytest_cache -o -name .ruff_cache -o -name dist -o -name build \
    \) -prune -o \( \
      -iname '*印度占星*' -o -iname '*jyotish*' -o -iname '*yinduzhanxing*' \
      -o -iname '*vedic*astro*' -o -iname '*vedastro*' \
      -o -iname '*dasha*shadbala*' -o -iname '*antigravity*round11*' \
    \) -print 2>/dev/null | head -n 200
done
```

## 输出报告 A：修复后透明度复核

输出文件：

- `docs/research/antigravity_round11_calibration_transparency_postfix_2026_06_25.md`

固定小节：

1. 对标
2. 开源参考
3. Bug

必须列出 P0/P1/P2 Bug 表；如果无 Bug，明确写“本轮未发现 P0/P1/P2 阻断问题”，并列剩余风险。

## 输出报告 B：GitHub 与本地碎片同步复核

输出文件：

- `docs/research/antigravity_round11_git_fragment_sync_postfix_2026_06_25.md`

必须包含表格：

| 项目 | 本地/远端状态 | 是否已同步 | 结论 |
|---|---|---|---|

至少覆盖当前主仓、远端 `codex/release-hygiene-ci`、`.workbuddy` 旧副本、`.gemini` scratch、Downloads PDF、Desktop 头像/报告、WorkBuddy 历史碎片。

## 输出报告 C：全球对标差距与下一优先级

输出文件：

- `docs/research/antigravity_round11_global_gap_next_priority_2026_06_25.md`

请按普通用户成品化排序，而不是按技术炫技排序。至少覆盖：

- VedAstro：API/MCP/技法数量和公共接口广度。
- JHora：桌面端传统深度、Dasha/Shadbala 绝对值黑盒真值。
- PyJHora：开源技法广度，但 AGPL 只能黑盒参考。
- 我们项目：AI Native、Trust Center、Evidence Validator、网页/app 技法承载、中文用户体验。

必须输出：

| 优先级 | 缺口 | 为什么影响普通用户 | Codex 下一步建议 |
|---|---|---|---|

## 输出报告 D：给 Codex 的 Round 12 任务建议

输出文件：

- `docs/research/antigravity_round11_codex_round12_recommendations_2026_06_25.md`

请给出 3-5 个可执行任务，并明确每个任务涉及的文件路径、测试命令和验收标准。

优先考虑：

1. 真实浏览器验证 Trust Center 新校准面板可见且移动端不溢出。
2. 把 Dasha/Shadbala 校准状态接入导出 HTML/JSON 报告。
3. 把 `oracle_collection_queue` 的 5 个采集任务做成普通人能照着填的表格/页面。
4. 准备第一批 JHora/PyJHora 外部截图证据包的手工录入模板。
5. 普通用户安装/启动路径继续降低摩擦。

## 最终回报格式

请在最终回复中用中文输出：

1. 已创建的文件列表。
2. GitHub 同步是否一致。
3. Web/App/Skill 校准透明度是否已修复。
4. 当前距离 VedAstro / JHora / PyJHora 仍差哪些。
5. Bug 表（P0/P1/P2，文件路径，行号或搜索 token，修复建议）。

结尾必须写：

> 下一步建议 Codex 优先……
