# Antigravity AI 质量门禁 Accuracy Profile 设计 (Round 24)

现有的 `quick` 和 `full` profile 仅仅是保障代码能跑，我们需要 `accuracy` profile 来保障“没算错”：

| 设计要点 | 具体方案 |
|---|---|
| 1. Profile 参数 | 增加 `python3 scripts/run_quality_gate.py --profile accuracy`。 |
| 2. 包含哪些 pytest | 必须包含 `tests/test_bphs_*.py`，`test_yoga_logic.py`，`test_ashtakoot.py`。 |
| 3. 排除哪些脚本 | 排除长耗时的打包脚本。 |
| 4. 跑 local_accuracy_report | 必须作为此 profile 的最后一关运行，拦截 F1 分数倒退。 |
| 5. 阻塞 Push 策略 | 建议仅在 `main` 的 pre-push hook 里开启 accuracy profile。 |
| 6. 运行时间预算 | 必须控制在 30 秒以内，确保开发者体验。 |
| 7. 失败信息展示 | 抛出红色的 `Accuracy Regression Detected`。 |
| 8. BPHS 不变量防线 | 只要 18 项不变量掉了一项，立刻 exit(1)。 |
| 9. 真人盘防线 | 66/66 gated charts 如果有一个因为修改计算公式算错了上升星座，立刻报错。 |
| 10. 容差范围 | Ashtakoot 得分必须精准到 0.01；位置必须精准到 120 arcsec。 |
| 11. Oracle 包络 | 如果 `valid_packets` 减少了（不兼容旧截图中提取的数据），报错。 |
| 12. Yoga F1 倒退阈值 | `F1 score` 不得低于 `0.950`。 |
| 13. UI 门禁 | 若跑此 profile，顺带用 Playwright 检查 `Ashtakavarga 337` 是否出现。 |
| 14. 静默模式 | 提供 `--quiet` 仅输出红绿灯不打日志。 |
| 15. 并发运行 | 使用 `pytest -n auto` 加速该门的通过。 |
| 16. 下一步落地 | 马上给 `run_quality_gate.py` 加入上述逻辑。 |

**副手下一轮任务**：写一份 `pytest-xdist` 引入的依赖审计方案，加速测试。
**Codex 可做任务**：在 `run_quality_gate.py` 中实际新增 `accuracy` 这一个 profile 分支。
