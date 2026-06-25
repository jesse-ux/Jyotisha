# Antigravity AI 质量门禁 CI 接入计划 (Round 25)

| 规划维度 | 实施说明 |
|---|---|
| 1. Github Action 文件 | `.github/workflows/ci.yml`。 |
| 2. 触发时机 | `on: [push, pull_request]` 对 `main` 和 `codex/` 分支。 |
| 3. 第一步检查 | 运行现有的 `python3 scripts/run_quality_gate.py --profile quick`。保障最基本的语法和编译正确。 |
| 4. 第二步检查 | 运行 `python3 scripts/run_quality_gate.py --profile accuracy`。 |
| 5. 退化拦截 | 如果发现 F1 分数或者不变量有任何掉分（导致 exit code 为 1），Workflow 将红叉。 |
| 6. 本地钩子 | 强烈建议使用 `pre-commit` hook 来拦截本地用户的 `git push`。 |
| 7. 速度权衡 | 因为 accuracy 不需要跑 Playwright 浏览器点击，所以即使是在弱机子上跑也应该极快（小于1分钟）。 |
| 8. 日志提取 | CI 可以抽取 `local_accuracy_report.py --format markdown` 的输出。 |
| 9. PR 评论 | 可以用第三方 Action 将上述 Markdown 当作 Comment 留在 PR 下方，让 Reviewer 一眼看到对准确度的影响。 |
| 10. 测试护栏 | `test_frontend_productization.py` 已经提前设下陷阱等待 Codex 去实现。 |
| 11. 与 release 区分 | Release profile 可以去跑极慢的 PWA 和 Tauri 打包检查。 |
| 12. 为什么不改代码 | 本文只提方案，不触碰具体实现文件，符合只读策略。 |
| 13. 下一步 Codex 1 | 🟢 Codex可做 | 新增一个 `.github/workflows/accuracy.yml`。 |
| 14. 下一步 Codex 2 | 🟢 Codex可做 | 在该 YAML 里用 `python3 -m pip install -r requirements.txt` 和 `python3 scripts/run_quality_gate.py --profile accuracy`。 |
| 15. 下一步 副手 | 🟢 副手继续做 | 分析如果本地用户强行用 `--no-verify` push，CI 该如何补刀。 |
| 16. 需要人工 | 🔴 否 | 自动化环境。 |
| 17. 代码路径 | `.github/workflows/` |
| 18. 最终判定 | 🟢 成立 | CI 补齐将是我们拒绝任何带有数学漏洞的代码合入最后一道保险。 |
