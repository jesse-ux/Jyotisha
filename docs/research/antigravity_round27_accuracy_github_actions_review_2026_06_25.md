# Antigravity AI GitHub Actions accuracy workflow 审查 (Round 27)

设计 `.github/workflows/accuracy.yml` 的最小且最高效的 YAML 草案：

| 设计项 | YAML 配置说明 |
|---|---|
| 1. 触发器 (on) | `push: branches: [ main, "codex/*" ]`, `pull_request: branches: [ main ]` |
| 2. 避免 Playwright | **必须**：这个 accuracy 门禁不依赖任何 UI 交互，它纯算力。安装 Playwright 会无端增加 5 分钟的 CI 耗时，坚决抵制。 |
| 3. Runner 环境 | `runs-on: ubuntu-latest` |
| 4. Python Setup | `uses: actions/setup-python@v4` with `python-version: '3.10'` |
| 5. 依赖缓存 | `cache: 'pip'`。能把 30 秒的装包时间压缩到 5 秒。 |
| 6. 安装极简包 | `run: pip install -r requirements.txt pytest` (千万别装 playwright/chromium)。 |
| 7. 运行门禁 | `run: python3 scripts/run_quality_gate.py --profile accuracy` |
| 8. 成功反馈 | Workflow 绿标。 |
| 9. 失败反馈 | 阻止 PR merge，红标。 |
| 10. 输出制品 | `run: python3 scripts/local_accuracy_report.py --format markdown >> $GITHUB_STEP_SUMMARY` |
| 11. Codex 任务 1 | 🟢 Codex可做 | 按照以上规格编写 `accuracy.yml` 并落盘。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 确保没有把 `playwright install` 抄进这个文件。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 给它命名为 `Astrology Engine Accuracy Gate`。 |
| 14. 副手下轮 1 | 🟢 副手可做 | 调研如何在一个单独的 `e2e.yml` 里单独跑 Playwright，做到动静分离。 |
| 15. 副手下轮 2 | 🟢 副手可做 | 设计 PR 机器人，在评论里打出 F1 分数的雷达图。 |
| 16. 副手下轮 3 | 🟢 副手可做 | 测试该 workflow 的语法是否通过了 GitHub 静态校验。 |
| 17. 需要人工 | 🔴 否 | |
| 18. TDD 哲学 | 越快，就越有人愿意跑。 |
| 19. 独立性 | 这让我们的引擎逻辑部分彻底摆脱了前端编译的羁绊。 |
| 20. 权限 | 最小化权限，只读即可。 |
| 21. 超时限制 | 加个 `timeout-minutes: 10` 防挂死。 |
| 22. Path Filter | `paths: ['scripts/**', 'tests/**', 'references/**']` (只在改了后端时才跑)。 |
| 23. 并发取消 | 配置 concurrency group，取消旧 push 的多余算力消耗。 |
| 24. 结果持久化 | 使用 actions/upload-artifact 存一下生成的 JSON。 |
| 25. 总结 | 这是高可信度开发的最后一块拼图。 |
