# Antigravity AI Ashtakoot VedAstro 表迁移安全方案 (Round 26)

| 迁移设计与风险控制 | 详细说明 |
|---|---|
| 1. License 确认 | VedAstro (https://github.com/VedAstro/VedAstro) 确认处于 MIT License 保护下。 |
| 2. 目标文件 | `Library/Logic/Calculate/MatchCalculator.cs`。 |
| 3. 可复制范围 | `CalculateVarna`, `CalculateVashya`, `CalculateTara`, `CalculateYoni`, `CalculateGrahaMaitri`, `CalculateGana`, `CalculateBhakoot`, `CalculateNadi` 中的常数和查表逻辑。 |
| 4. 不可复制范围 | 它的类结构、HTTP 返回包裹、或者跟其它组件耦合的 Entity 类。 |
| 5. 迁移容器 | 在我们这边新建 `scripts/ashtakoot_constants.py`。 |
| 6. 代码映射 (枚举) | C# 的 `enum ZodiacName` 需映射为我们的 `['Aries', 'Taurus', ...]` 字符串数组。 |
| 7. 代码映射 (星宿) | C# 的 `enum LunarMansionName` 需映射为我们的 `['Ashwini', 'Bharani', ...]`。 |
| 8. 代码映射 (分数) | 直接搬运 `double` 类型的常量，如 `7.0`, `1.5` 等。 |
| 9. 特殊例外规则 | Nadi 有“如果是相同星座但不同 Quarter 则得分”的例外，需特别搬运。 |
| 10. 回滚策略 | 不删除原有的基于简单判断的伪代码，而是用注释隔开，如果新字典算挂了可以迅速回切。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 新建 `scripts/ashtakoot_constants.py`，写上 MIT License 声明注释。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 将 VedAstro 的 Yoni 动物敌对矩阵转换为 Python 字典：`YONI_ENEMIES = { "Horse": ["Buffalo", ...], ... }`。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 在 `ashtakoot.py` 中引入这些新字典，并在算分时覆盖旧的 mock 返回值。 |
| 14. 副手下轮 1 | 🟢 副手继续做 | 如果算出的总分超过了 36，由我负责去比对哪条规则的上限越界了。 |
| 15. 副手下轮 2 | 🟢 副手继续做 | 验证 VedAstro 中对 Bhakoot 的计分是否包含了“相差7宫得7分”的规则。 |
| 16. 需要人工 | 🔴 否 | |
| 17. 为什么要做 | 因为目前这部分是伪造的 0 分，或者残缺的假分。 |
| 18. 风险点 | C# 的索引可能是 1-based 或者有奇怪的偏移，转 Python 字典时容易错位。 |
| 19. 测试覆盖 | 在改完后，必须保证 `tests/test_ashtakoot.py` 里的假数据测试通过。 |
| 20. 总结 | 这是合婚功能从“壳子”到“真核”的唯一通途。 |
