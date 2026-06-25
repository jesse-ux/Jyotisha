# Antigravity AI 当前补丁后 Artifact 存档规范复核 (Round 18)

| 检查项 | 结论 | 证据/说明 |
|---|---|---|
| 1. `references/oracle/artifacts/README.md` 是否存在 | 🔴 未成立 | `git status` 与 `rg` 均未发现该文件。 |
| 2. 是否存在 `.gitkeep` 占位 | 🔴 未成立 | 目录未被 Git 追踪。 |
| 3. `README.md` 是否公开写明归档目录 | 🔴 未成立 | 缺少 README。 |
| 4. `source_artifact` 是否限定脱敏 | 🔴 未成立 | 代码/文档中均无强制脱敏约束被落实。 |
| 5. 是否出现 `external_oracle_artifact` | 🔴 未成立 | 源码中无此关键字。 |
| 6. 是否明确“必须打码” | 🔴 未成立 | 全局搜索 `必须打码` 在源码和非副手报告中命中为 0。 |
| 7. 是否明确“不得提交私人 PDF 原件” | 🔴 未成立 | 未防护。 |
| 8. 是否明确“不得提交完整出生报告” | 🔴 未成立 | 未防护。 |
| 9. 是否明确“浏览器 scratch” 不可提交 | 🔴 未成立 | 未防护。 |
| 10. Web 下载证据包提示 | 🔴 未成立 | `jyotish-app/main.js` 中没有针对 artifact 路径打码的提示。 |
| 11. 其它高风险本地输出 | 🔴 部分成立 | `.gitignore` 已包含 `output_report`，但可能漏掉其它临时文件。 |
| 12. 伪装成本地计算输出的风险 | 🔴 存在 | 缺乏物理图片和打码对照，容易造假。 |

**落地建议**：Codex 必须在 `jyotish-app/main.js` 下载 JSON 的逻辑里插入弹窗提示，并创建 `references/oracle/artifacts/README.md`。
