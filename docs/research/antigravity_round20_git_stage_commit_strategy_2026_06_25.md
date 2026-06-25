# Antigravity AI Git 纳入与提交策略复核 (Round 20)

| 审计维度 | 当前状态与建议 |
|---|---|
| 1. Modified 文件列表 | `.gitignore`、`jyotish_api_server.py`、`jyotish_engine.py`、`oracle_evidence_validator.py`、`tests/*`、`main.js`。 |
| 2. Untracked 文件列表 | 主要是我生成的 `docs/research/antigravity_round19_*.md` 和 `antigravity_round20_*.md` 报告。 |
| 3. 产品代码必须纳入 | 🟢 必须 `git add scripts/ tests/ jyotish-app/`。 |
| 4. 副手报告必须纳入 | 🟢 必须 `git add docs/research/` 留档快照。 |
| 5. policy/template 纳入 | 🟢 已经纳入并在修改。 |
| 6. 哪些不应纳入 | 🟢 临时 HTML 和缓存文件已被 `.gitignore` 过滤。 |
| 7. runtime HTML 忽略 | 🟢 是，刚在补丁中完成忽略。 |
| 8. 私人文件污染 | 🟢 未检出。 |
| 9. 建议 stage 清单 | `git add .` （由于 `.gitignore` 已修好，当前工作树下全部变动都是安全可提交的）。 |
| 10. Commit Message | `chore(oracle): enforce shadbala non-negative validation and sync round 19-20 sidecar research` |
| 11. 是否需要 Push | 🟡 强烈建议 Push，不要让巨量报告堆在本地。 |
| 12. 风险提示 | 在人工放入 JHora 截图前，别把用户的真图忘打码就 add 了。 |

**落地建议**：现在 `.gitignore` 已经天衣无缝，Codex 可以放心地一键 `git commit -a -m "..."`。
