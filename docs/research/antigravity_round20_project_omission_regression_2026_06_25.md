# Antigravity AI 全项目遗漏风险回归 (Round 20)

| 复核项 | 状态 | 结论与动作 |
|---|---|---|
| 1. Round 16-20 work orders | 🟡 遗漏跟踪 | `docs/research/` 目录下的大量单据未被 `git add`，必须马上提仓。 |
| 2. Round 16-20 reports | 🟡 遗漏跟踪 | 全部报告均为 Untracked，快要攒到 40 份了，必须立刻 Commit。 |
| 3. `user_jhora_capture_guide.md` | 🟢 安全 | 早已在之前的 commit 中纳入。 |
| 4. `artifacts/README.md` | 🟢 安全 | 已经存在且已跟踪。 |
| 5. `evidence_packet_templates` | 🟢 安全 | 已跟踪。 |
| 6. Ashtakoot 报告与代码冲突 | 🟢 已纠偏 | 本轮已纠正 Round 19 误判的“未开发”论点。 |
| 7. `.gitignore` | 🟢 完美 | 已经把 HTML 堵死了。 |
| 8. `task_plan.md` / `progress.md` | 🟢 安全 | 有定期更新机制。 |
| 9. 真人 1/5 的 JHora 图 | 🔴 严重阻塞 | 这个事被一遍一遍地推延，导致系统一直卡在 `valid_packets: 0`。 |
| 10. 必须纳入 Git 的最小集合 | 🟡 行动点 | `git add docs/research/`，否则换个工作树我的调研就全没了。 |

**落地建议**：Codex 下一步第一件事就是 `git commit`。第二件事就是抓个人来跑 JHora！
