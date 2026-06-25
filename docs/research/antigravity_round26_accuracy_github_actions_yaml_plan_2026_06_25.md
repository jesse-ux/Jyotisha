# Antigravity AI Accuracy GitHub Actions YAML 方案 (Round 26)

| 规划项 | YAML 配置与设计 |
|---|---|
| 1. 文件路径 | `.github/workflows/accuracy.yml` |
| 2. 触发条件 | `on: push: branches: [ main, codex/* ]` 以及 `pull_request:` |
| 3. 环境配置 | `runs-on: ubuntu-latest` |
| 4. Python 版本 | `uses: actions/setup-python@v4` with `python-version: '3.10'` |
| 5. 缓存依赖 | `cache: 'pip'` 加速 `pip install` |
| 6. 安装依赖 | `run: pip install -r requirements.txt` 和 `pip install pytest pytest-xdist playwright` |
| 7. 跑底层验证 | `run: python3 scripts/run_quality_gate.py --profile accuracy` |
| 8. 如果通过 | 正常结束，PR 显示绿勾。 |
| 9. 如果报错 | Workflow 自动阻断，要求作者去本地修 Yoga 逻辑或引擎。 |
| 10. Markdown 生成 | `run: python3 scripts/local_accuracy_report.py --format markdown > report.md` |
| 11. 上传 Artifact | `uses: actions/upload-artifact@v3` 传这个 `report.md` |
| 12. Job 命名 | `name: Astrology Engine Accuracy Gate` |
| 13. 并发控制 | `concurrency: group: ${{ github.ref }}` 保证新 push 取消旧的。 |
| 14. 保护分支 | 必须在 repo settings 里勾选 `Require status checks to pass before merging`。 |
| 15. Codex 任务 1 | 🟢 Codex可做 | 创建这个 `accuracy.yml` 文件。 |
| 16. Codex 任务 2 | 🟢 Codex可做 | 加入一段命令：把 `report.md` 作为 step summary 输出到 GitHub 面板上。 |
| 17. Codex 任务 3 | 🟢 Codex可做 | 把 `pytest-xdist` 顺带写入 `requirements.txt` 以支持多线程跑测试。 |
| 18. 副手任务 1 | 🟢 副手继续做 | 去了解有没有 Action 可以在 PR 里把 F1 退步的项作为 Comment 发出来。 |
| 19. 副手任务 2 | 🟢 副手继续做 | 调研如何仅在相关 Python 文件改动时才触发此 workflow。 |
| 20. 需人工外力 | 🔴 否 | 纯自动化。 |
