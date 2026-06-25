# Antigravity AI Git Stage/Commit 最小风险策略 (Round 21)

当前 Untracked 报告积累量极大（40+份），建议执行双段 Commit：

| 策略步骤 | 细节说明 |
|---|---|
| 1. 建议分几次 commit | 强烈建议分 **2 次**。一次给代码产品，一次给研究文档。 |
| 2. Commit 1 包含内容 | `.gitignore`、`oracle_evidence_validator.py` 等在工作树中 modified 的核心文件。 |
| 3. Commit 2 包含内容 | 把 `docs/research/antigravity_round16-*` 到 `round21-*` 一次性打包入库。 |
| 4. 是否一次纳入报告 | 是。否则下次换个沙箱就彻底丢了。 |
| 5. 排除文件 | `.tempmediaStorage`，以防万一。 |
| 6. `git add` 确切命令 | `git add scripts/ tests/ jyotish-app/ .gitignore` (第一次)；`git add docs/research/antigravity_*` (第二次)。 |
| 7. 检查变更 | `git diff --cached --stat`。 |
| 8. Commit Message 1 | `fix(oracle): enforce shadbala non-negative validation and sync oracle progress` |
| 9. Commit Message 2 | `docs(research): archive round 16 to 21 extensive architectural analysis and sidecar reports` |
| 10. SSH 443 应对 | 如果连 Github 443 端口超时，不要管它，只要本地 commit 成功就行。 |
| 11. Update-ref 需求 | 无。 |
| 12. 回滚风险 | 如果不赶紧 commit，一旦 Codex 被要求“重构所有文档”，这几十万字的调研结晶瞬间就没了。 |

**最小 Codex 改动建议**：按照上面的两步走，立刻结束工作树的 Untracked 脏状态。
