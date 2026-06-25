# Antigravity AI VedAstro Ashtakoot 常量深挖 (Round 22)

| 检索要点 | 结论记录 |
|---|---|
| 1. URL | `https://github.com/VedAstro/VedAstro` |
| 2. License | `MIT License`，安全！ |
| 3. 目标代码路径 | `VedAstro.Library/MatchCalculator.cs` |
| 4. 方法名 | 包含 `CalculateVarna`, `CalculateVashya` 等。 |
| 5. Varna 常量 | 基于 Rashi 的 Brahmin, Kshatriya, Vaishya, Shudra 四分法。 |
| 6. Vashya 常量 | 基于 Rashi 的控制关系矩阵。 |
| 7. Tara 计算 | `(boy_nak - girl_nak) % 9` 的距离映射。 |
| 8. Yoni 常量 | 14 种动物的冲突矩阵（Cow vs Tiger 等）。 |
| 9. Graha Maitri | Rashi 主星（Sun, Moon...）之间的敌友矩阵（5分）。 |
| 10. Gana 常量 | Deva, Manushya, Rakshasa 组合得分（6分）。 |
| 11. Bhakoot 常量 | 基于 Rashi 相对距离（如 6-8, 2-12 是 0分，其他是 7分）。 |
| 12. Nadi 常量 | Adi, Madhya, Antya 冲突得 0，否则 8 分。 |
| 13. Kuja/Manglik | 提供 `CalculateKujaDosha`。 |
| 14. 依赖 | 高度依赖其自身构建的 `ZodiacSign` 和 `ConstellationName` 枚举。 |
| 15. C# 到 Python | 将上述 C# 的判断逻辑提取为纯粹的 Python 字典查询或简单的 if-else 函数。 |
| 16. Attribution | 在代码顶部写明：`Based on constants from VedAstro (MIT License)`。 |
| 17. 引入依赖 | 不需要，C# 库无法直接引，只能扒逻辑。 |
| 18. License 冲突 | 无。 |

**最小 Codex 改动建议**：这部分逻辑太厚了，下一轮由我（副手）或大模型将其转写为 Python 草稿 `ashtakoot_constants.py` 给 Codex。
