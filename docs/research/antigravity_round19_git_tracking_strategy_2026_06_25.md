# Antigravity AI Git 远端/未跟踪文件纳入策略 (Round 19)

| 检查项 | 结论 | 证据/说明 |
|---|---|---|
| 1. 当前 branch | `main` (或开发主分支) | `git status` 显示。 |
| 2. ahead/behind | ahead 若干 commit | 本地包含了近期大量的提交，尚未 Push（或者正在 PR）。 |
| 3. Round 16-19 报告/单子 | 🟡 未跟踪 | 我的生成物均落在 `docs/research/` 且大部分未 `git add`。 |
| 4. artifacts README | 🟢 已跟踪 | `git log` 显示已 Commit。 |
| 5. guide | 🟢 已跟踪 | 包含在之前 Codex 补丁里。 |
| 6. template | 🟢 已跟踪 | 包含在之前 Codex 补丁里。 |
| 7. 哪些必须纳入 Git | 🟡 行动点 | 所有我生成的 `antigravity_round19_*.md` 报告都应 `git add docs/research/`，作为知识库长久沉淀。 |
| 8. 哪些不应纳入 Git | 🟢 已成立 | `runtime-smoke-report-*.html`，以及用户的私人截图（目前还没有）。 |
| 9. 是否存在敏感文件 | 🟢 未检出 | 审查无误。 |
| 10. Codex 最小 stage 清单 | 🟡 行动点 | `git add .gitignore docs/research/`。 |
| 11. 是否需要推送 | 🟡 建议 | 在 `git commit -m "docs: add round 19 research reports"` 后执行 `git push` 同步到云端，避免本地丢失。 |

**落地建议**：Codex 在做完 `.gitignore` 修改后，请全量把我的 14 份报告连同 `.gitignore` 一起 Commit 掉。
