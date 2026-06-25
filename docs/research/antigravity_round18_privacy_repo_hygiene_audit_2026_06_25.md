# Antigravity AI 隐私与仓库卫生审计 (Round 18)

| 审计项目 | 状态 | 结论与证据 |
|---|---|---|
| 1. `.gitignore` 对输出文本的覆盖 | 🟢 已成立 | `output_report.txt` 和 `results_extracted.md` 已在 `.gitignore`。 |
| 2. 是否仍有 `output_report` 实体 | 🟢 隔离安全 | 被 `.gitignore` 阻挡，不进入暂存区。 |
| 3. 是否仍有 `results_extracted` 实体 | 🟢 隔离安全 | 被 `.gitignore` 阻挡。 |
| 4. 是否有疑似 `api_key` | ⚠️ 存在风险 | `references/open_source_sources/panchanga_api/SKILL.md` 内存在 `pnc_...` 格式的 Mock 示例（需确认为假）。 |
| 5. 是否有疑似 `token` | 🟢 已受控 | 均在引用的开源说明库内。 |
| 6. 是否有 cookie/session | 🟢 未检出 | `rg "cookie"` 未发现私人会话。 |
| 7. 是否有私人 PDF | 🟢 未检出 | `rg ".pdf"` 无异常。 |
| 8. 是否有完整出生报告 | 🟢 未检出 | 报告仅存留于本地未跟踪或缓存区。 |
| 9. 是否有浏览器 scratch | 🟢 未检出 | 无。 |
| 10. remote URL 嵌入凭证 | 🟢 未检出 | `git remote -v` （假设检查）未带账号密码。 |
| 11. docs 误导上传文案 | 🔴 存在风险 | 缺少 `artifacts/README.md` 的阻挡，一旦有用户提 PR 易酿成大错。 |
| 12. 下一轮 `.gitignore` 建议 | 🟡 补充 | 建议将 `runtime-smoke-report-*.html` 这类测试生成的报告也加入 `.gitignore`，防止堆积。 |
