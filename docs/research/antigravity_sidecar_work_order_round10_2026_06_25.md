# Antigravity AI 副手任务单 Round 10（2026-06-25）

## 任务目标

本轮副手任务聚焦两件事：

1. 复核“地毯式本机碎片扫描”和 GitHub 云端同步状态，确认是否还有因 Codex、Antigravity、WorkBuddy、Downloads、Desktop、历史备份窗口造成的印度占星文件遗漏。
2. 复核 Round 9 暴露的普通用户风险：Web/App/Skill 是否仍没有清晰披露 Dasha/Shadbala 外部校准状态。

本轮仍然是外部审计和黑盒验证任务，不是核心实现任务。Codex 主线程会负责真正修改 `jyotish-app`、`SKILL.md`、测试和提交推送。

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 GitHub token、API key、浏览器登录态、系统钥匙串、cookie、SSH 私钥或远端凭证。
- 不要打开或摘录用户私人星盘完整报告内容，除非只读取文件名、大小、路径和同步状态。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/`、`README.md` 的实现内容。
- 不要把 `output_report.txt`、`results_extracted.md` 或任何私人出生资料推送/纳入同步建议。
- 不要复制 JHora、PyJHora、AGPL/GPL 项目的实现代码、公式常量或内部数据表。
- 不要把 `template_only`、`local_baseline`、本仓库输出或空目标字段标成 `external_verified`。
- 不要使用“绝对可信”“世界第一”“完全校准”等过度准确率话术。

允许事项：

- 可以读取 `README.md`、`SKILL.md`、`task_plan.md`、`findings.md`、`progress.md`。
- 可以读取 `docs/research/*round8*`、`docs/research/*round9*` 和本任务单。
- 可以读取 `scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`scripts/oracle_boundary_audit.py` 和 `references/oracle/dasha_shadbala_oracle_cases.json`。
- 可以运行只读命令：`git status`、`git log`、`git ls-remote`、`find`、`rg`、`python3 ... --format json`、`pytest`。
- 可以联网查询公开对标资料，但只做产品差距和许可证边界分析，不复制代码。
- 只能新增 `docs/research/*round10*2026_06_25.md` 报告文件。

## 必跑命令

### 1. 当前仓库状态

```bash
git status --short --branch
git log --oneline --decorate -n 8
git remote -v
```

### 2. GitHub 远端真实 HEAD

优先用 443 端口，避免普通 SSH 22 端口超时：

```bash
GIT_SSH_COMMAND='ssh -p 443 -o ServerAliveInterval=10 -o ServerAliveCountMax=3' \
git ls-remote ssh://git@ssh.github.com:443/732642856/yinduzhanxing.git \
  refs/heads/codex/release-hygiene-ci refs/heads/main
```

必须判断：

- 本地 `HEAD` 是否等于远端 `refs/heads/codex/release-hygiene-ci`。
- 本地 `origin/...` 跟踪引用是否只是没有 fetch 更新。
- 是否有未跟踪文件应归档、提交或忽略。

### 3. 本地高相关碎片扫描

只扫描文件名/路径，不读取私人报告正文：

```bash
for base in \
  <home>/Documents \
  <home>/Downloads \
  <home>/Desktop \
  <home>/Projects \
  <home>/WorkBuddy \
  <home>/.workbuddy \
  <home>/.codex \
  <home>/.gemini \
  <home>/engines-repo \
  <home>/文件仓库
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
      -o -iname '*dasha*shadbala*' -o -iname '*antigravity*round*' \
    \) -print 2>/dev/null | head -n 200
done
```

### 4. 本地同项目 Git 副本扫描

```bash
find <home> -type d -name .git \
  \( -path '*/node_modules/*' -o -path '*/Library/*' -o -path '*/.Trash/*' \) -prune \
  -o -type d -name .git -print 2>/dev/null \
  | sed 's#/.git$##' > /tmp/all_git_repos_round10.txt

while IFS= read -r repo; do
  if git -C "$repo" remote -v 2>/dev/null | grep -E '732642856/yinduzhanxing|yinduzhanxing' >/dev/null; then
    echo "--- $repo"
    git -C "$repo" remote -v
    git -C "$repo" status --short --branch | head -n 8
    git -C "$repo" log --oneline -n 5 2>/dev/null
  fi
done < /tmp/all_git_repos_round10.txt
```

### 5. Oracle / calibration gate 复验

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round10.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round10.json
```

```bash
python3 -B -m pytest \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated \
  -q
```

### 6. Web/App/Skill 透明度静态复核

```bash
rg "ready_for_calibration|Dasha/Shadbala|external_oracle_evidence_validation|calibration|校准|Evidence Validator" \
  README.md SKILL.md jyotish-app docs/research -n
```

## 对标任务 A：全球对标项目差距复核

输出文件：

- `docs/research/antigravity_round10_global_benchmark_gap_recheck_2026_06_25.md`

必须参考公开资料并用中文总结：

- VedAstro / VedAstro.Python：公开 README 宣称 596 calculations，MIT license，适合作为 API/AI/MCP 广度对标。
- PyJHora：AGPL-3.0，特性广，适合作为黑盒 oracle/行为参考，不可复制实现代码。
- JHora / Jagannatha Hora：桌面端深度标杆，重点作为截图/人工录入的 Dasha/Shadbala 外部真值来源。
- Hora Prakash 或其他开源网页产品：用于普通用户交付形态、无账号/离线/浏览器体验对标。

输出固定小节：

1. 对标
2. 开源参考
3. Bug

## 本机同步任务 B：本地碎片与主仓差异审计

输出文件：

- `docs/research/antigravity_round10_local_fragment_sync_audit_2026_06_25.md`

必须按表格输出：

| 类别 | 路径 | 状态 | 是否应同步到主仓 | 理由 |
|---|---|---|---|---|

至少覆盖：

- 当前主仓 `<repo>`
- `.workbuddy/skills/jyotish-vedic-astrology`
- `.gemini/antigravity-ide/.../scratch`
- `Downloads/印度占星*.pdf`
- `Desktop` 上的解盘报告或头像图片
- `WorkBuddy/2026-06-09-20-03-34/jyotish-fragments`
- `Projects/星轨资料恢复/.../jyotish-vedic-astrology`
- `Documents/Codex/.../yinduzhanxing...`
- `Documents/星轨talk/engines-repo/jyotish`

判断口径：

- 产品代码、测试、公开研究报告：可能应同步。
- 私人星盘输出、PDF 原件、Antigravity scratch、临时 stdout：默认不推送。
- 历史 skill 副本：只做差异来源，不直接覆盖当前主仓。
- 下载区压缩包：除非包含新模块且许可证清楚，否则只记录，不纳入主仓。

## 云端同步任务 C：GitHub 状态复核

输出文件：

- `docs/research/antigravity_round10_git_cloud_sync_blackbox_2026_06_25.md`

必须回答：

- `codex/release-hygiene-ci` 远端 HEAD 是什么 commit。
- 本地 HEAD 是什么 commit。
- 本地 `origin/codex-release...` 如果显示 ahead，是否只是 local tracking ref stale。
- 当前未跟踪文件中哪些应该提交，哪些应该保留本地。
- 是否发现其他本机同 remote 的仓库副本存在未同步提交。

## 产品透明度任务 D：Round 9 P0/P1 复核

输出文件：

- `docs/research/antigravity_round10_calibration_transparency_recheck_2026_06_25.md`

必须检查：

- Web/App Trust Center 是否已经展示 Dasha/Shadbala Calibration Status。
- AI Chat 是否已经强制注入 “Dasha/Shadbala 仍在外部 evidence validator 校准中，不做绝对断言”。
- `SKILL.md` 是否明确要求普通用户解释时区分 D1/D9 高可信与 Dasha/Shadbala 待外部校准。
- 若尚未修复，输出 P0/P1/P2 Bug 表。

## 给 Codex 的下一步任务 E

输出文件：

- `docs/research/antigravity_round10_next_codex_fix_queue_2026_06_25.md`

必须给出可执行顺序：

1. 先处理 Git 同步与本地未跟踪 Round 9/Round 10 文档，排除 `output_report.txt`、`results_extracted.md`。
2. 给 Web/App Trust Center 增加 Dasha/Shadbala Calibration Status。
3. 同步 AI Chat prompt boundary 与 `SKILL.md`。
4. 增加静态/前端测试，防止校准状态再次从普通用户界面消失。
5. 继续采集 JHora/PyJHora 黑盒真值，直到至少 3 条 evidence packet 通过 validator。

## 最终回复格式

完成后在 Antigravity 聊天里用中文回复：

1. 已创建哪些 `docs/research/*round10*2026_06_25.md` 文件。
2. 本机是否发现未同步的印度占星文件碎片，哪些应提交、哪些应忽略。
3. GitHub 远端 `codex/release-hygiene-ci` 是否与本地 HEAD 对齐。
4. Web/App/Skill 是否已充分披露 Dasha/Shadbala 校准状态。
5. P0/P1/P2 Bug 总表。
6. 下一步建议给 Codex 的可执行修复事项。

最终报告必须包含三个固定章节：

- 对标
- 开源参考
- Bug

## 公开参考源

- VedAstro.Python GitHub：`https://github.com/VedAstro/VedAstro.Python`
- VedAstro AI Docs：`https://vedastro.org/DocsForAI.html`
- PyJHora GitHub：`https://github.com/naturalstupid/PyJHora`
- JHora 官方页面：`https://www.vedicastrologer.org/jh/`
- Jagannatha Hora 新站：`https://jagannathahora.com/`
- Hora Prakash GitHub：`https://github.com/PriyankGahtori/hora-prakash`
