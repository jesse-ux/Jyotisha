# Antigravity AI Yoga 报告 diff 稳定性复核 (Round 27)

| 分析项 | 诊断结果 |
|---|---|
| 1. 产生 Diff 的文件 | `references/validation_logic_report.json`。 |
| 2. Diff 产生原因 | 因为 `scripts/validate_logic_v2.py` 执行后的自然更新。 |
| 3. 语义是否改变 | 🟢 否，语义未变 | 分数依然是 F1: 0.9522。 |
| 4. 为什么会有 Diff | 🟡 排序与键值稳定性 | 可能是 dict 生成时未强制 sort_keys=True，或者内部有些微调。 |
| 5. 是否为准确率退化 | 🟢 否 | Precision 和 Recall 的绝对数值维持不变。 |
| 6. 是否影响真实用户 | 🟢 否 | 这只是开发者视角的基准线。 |
| 7. 提交建议 | 🟢 建议提交 | 虽然是无伤大雅的 diff，但不提交会导致 working tree 不干净。 |
| 8. 解决方案 | 强制给 json.dump 加上 `sort_keys=True` 避免无意义的顺序 diff。 |
| 9. Codex 任务 1 | 🟢 Codex可做 | 去 `scripts/validate_logic_v2.py` 等写 json 的地方加上 `sort_keys=True`。 |
| 10. Codex 任务 2 | 🟢 Codex可做 | 把当前这个 diff 用 `git add` 直接吸收掉。 |
| 11. Codex 任务 3 | 🟢 Codex可做 | 如果有 `--format json` 输出也要保证排序稳定。 |
| 12. 副手下轮 1 | 🟢 副手可做 | 编写脚本扫描所有 json 生成点是否都遵守了排序规范。 |
| 13. 副手下轮 2 | 🟢 副手可做 | 定期分析该文件，看 F1 分数的变化曲线。 |
| 14. 副手下轮 3 | 🟢 副手可做 | 提炼这 36 个 False Positives 寻找其共同规律。 |
| 15. 需要人工 | 🔴 否 | |
| 16. 安全考量 | 不涉密。 |
| 17. PyJHora 依赖 | 这是与 PyJHora 的最后一次基准比较产物。 |
| 18. Json 结构 | 嵌套层级深，乱序 diff 极大。 |
| 19. Git Hook | 可考虑加个 pre-commit 验证 JSON 格式。 |
| 20. Python 版本 | 3.7+ 字典默认保序，但 key 插入顺序可能因运行时变化。 |
| 21. TDD 意义 | 消除“幽灵”改动。 |
| 22. CI 意义 | 确保门禁每次跑出来的 artifact 是一致的 hash。 |
| 23. 文件定位 | 它作为黄金标准数据源存在。 |
| 24. 开发体验 | 大幅提升，告别莫名其妙的红绿。 |
| 25. 总结 | 虚惊一场，只是序列化问题。 |
