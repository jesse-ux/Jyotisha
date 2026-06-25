# Antigravity AI runtime-smoke HTML 与本地输出卫生审计 (Round 19)

| 检查项 | 结论 | 证据/说明 |
|---|---|---|
| 1. `.gitignore` 屏蔽 smoke HTML | 🔴 未成立 | 测试运行留下了 `runtime-smoke-report-*.html` 未被屏蔽。 |
| 2. 未跟踪 smoke HTML | 🔴 存在 | 目录中出现了 `runtime-smoke-report-20260625-*.html` 垃圾。 |
| 3. 是否存在 `output_report.txt` | 🟢 已成立 | 已被 ignore。 |
| 4. 是否存在 `results_extracted.md` | 🟢 已成立 | 已被 ignore。 |
| 5. 私人 PDF | 🟢 未检出 | 全局无此后缀的污染。 |
| 6. 完整出生报告 | 🟢 未检出 | 报告未上云。 |
| 7. 浏览器 scratch | 🟢 未检出 | 不存在缓存截取目录。 |
| 8. artifacts 目录污染 | 🟢 未检出 | 目前该目录下除了 `.gitkeep` 与 `README.md`，尚无人类乱塞的截屏。 |
| 9. dist 构建产物 | 🟢 已成立 | `dist/` 与 `jyotish-app/dist/` 都在黑名单。 |
| 10. 最小 `.gitignore` 建议 | 🟡 行动点 | `echo "runtime-smoke-report-*.html" >> .gitignore` |

**落地建议**：Codex 必须立刻修改 `.gitignore`，将那几份刚生成的 html 屏蔽，避免提交污染。
