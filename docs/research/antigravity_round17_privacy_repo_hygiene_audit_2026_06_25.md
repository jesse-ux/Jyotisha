# Antigravity AI 隐私与仓库卫生专项审计 (Round 17)

通过对仓库使用 `git status --short` 及 `rg` 进行全局检索，我们发现了若干具有强隐私或数据污染倾向的隐患：

| 风险 | 路径或 token | 是否已防护 | 建议 |
|---|---|---|---|
| **API 密钥明文** | `references/open_source_sources/panchanga_api/SKILL.md` 等 | ⚠️ **部分暴露** | 外部参考库的文档里包含如 `api_key: "pnc_..."` 的伪造或真实示例 token。需确认仅为文档 mock。 |
| **本地生成报告** | `output_report.txt`, `results_extracted.md` | 🔴 **未防护** | 虽然不在源码目录，但由于未在 `.gitignore` 锁定，很容易被误 `git add` 送上云端，泄露测算目标人隐私。必须加入 `.gitignore`。 |
| **PDF 个人命盘** | `birth report` | 🟢 **已受控** | 目前仅有测试生成记录，无真实用户的完整 PDF 落盘至仓库。需在 Artifact 规范里补充“不得上传”。 |
| **JHora 证据图片** | `references/oracle/artifacts` | 🔴 **未防护** | 目录没建，规范没写，如果用户提 PR 包含未打码的高清生辰截图，将永久污染 Git 历史。必须马上出台文档。 |
| **OCR 乱码等** | `references/.../jaimini-tropical/...` | 🟢 **安全** | 只是一些外部双语文献格式化脚本的执行垃圾，属于可控工具。 |

**审计结论**：当前本地目录中存在大量的 `docs/research/*.md` （由我副手生成，这些是好的），但对于临时命盘输出 `output_report` 以及即将涌入的 `artifacts` 图片，系统犹如“不设防的城池”。需立刻补强 `.gitignore` 与安全公约。
