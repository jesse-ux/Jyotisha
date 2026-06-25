# Antigravity AI VedAstro MIT 可复制范围精确核验 (Round 25)

| 检索项目 | 核查记录 |
|---|---|
| 1. 仓库 URL | `https://github.com/VedAstro/VedAstro` |
| 2. LICENSE URL | `https://github.com/VedAstro/VedAstro/blob/master/LICENSE` |
| 3. 具体文件路径 | `VedAstro/Library/Logic/Calculate/MatchCalculator.cs` |
| 4. 相关函数/类名 | `CalculateTara`, `CalculateYoni`, `CalculateNadi`, `CalculateBhakoot` 等。 |
| 5. 是否 MIT | 🟢 是的。可以自由取用。 |
| 6. Ashtakoot 常量 | 🟢 完全包含。所有的计分表（如 Nadi 分类，Gana 敌友）硬编码在文件里。 |
| 7. Panchang/Tithi | 🟢 包含。在 `VedAstro/Library/Logic/Calculate/Panchanga.cs` 等。 |
| 8. Shadbala | 🟢 包含。有很详细的 Rupa 计算。 |
| 9. C# 到 Python 风险 | 🟡 中。存在一些数据结构的跨语言翻译偏差（如 enum 映射）。 |
| 10. 哪些可复制 | 纯粹的矩阵、常量表、查表逻辑的判定树 (if-else/switch)。 |
| 11. 哪些只可参考 | 它的 HTTP API、前端 Blazor 代码结构，不可直接用。 |
| 12. Tithi/Karana 检索 | `CalculateTithi` 方法中运用了日月度数差除以 12 的传统逻辑。 |
| 13. Shadbala Sthana 检索| `CalculateSthanaBala` 中对于落宫力量的权重分配。 |
| 14. 极地出生处理 | 发现其在处理高纬度 Ascendant 时也有防御机制。 |
| 15. Ayanamsa 体系 | 默认 Lahiri，但也内置了多套。 |
| 16. 下一步 Codex | 🟢 Codex可做 | 将 `Panchanga.cs` 中的 Tithi 和 Karana 数学运算式平移到我们的 `scripts/panchang.py` 中。 |
| 17. 下一步 Codex 2 | 🟢 Codex可做 | 将 `MatchCalculator.cs` 中的同星宿 Nadi 豁免规则（例外处理）复制过来。 |
| 18. 下一步 副手 | 🟢 副手继续做 | 做一个中英对照的术语映射词典，将 VedAstro 的变量名映射到我们的代码体系中。 |
