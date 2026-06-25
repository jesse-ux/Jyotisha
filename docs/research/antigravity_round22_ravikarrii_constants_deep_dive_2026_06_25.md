# Antigravity AI RaviKarrii MIT Java 常量深挖 (Round 22)

| 检索要点 | 结论记录 |
|---|---|
| 1. License | MIT License。 |
| 2. Java package 结构 | `com.astrology.compatibility`。 |
| 3. 输入字段 | `boyStar`, `girlStar`, `boySign`, `girlSign`。 |
| 4. 输出字段 | 8 Kuta 的单项得分与 `totalScore`。 |
| 5. 8 Kuta 常量 | 提取在 `ScoreCalculator` 等类的方法硬编码中。 |
| 6. 总分计算 | 将 8 个 Kuta 的分值简单相加。 |
| 7. Nakshatra 映射 | 含有枚举。 |
| 8. Rashi 映射 | 含有枚举。 |
| 9. 测试样本 | 包含了一些 Junit Tests。 |
| 10. API 示例 | `/api/v1/match` POST 请求。 |
| 11. 是否可复制 | 🟢 是，常量数组可复制。 |
| 12. 与 VedAstro 差异 | VedAstro 有更全面的异常豁免处理（例如 Nadi 的 exception），而该库比较直板。 |
| 13. 最小可移植文件 | 只需移植其中 27x27 的矩阵计算函数即可。 |
| 14. 风险等级 | 低风险。 |

**最小 Codex 改动建议**：备用方案。首选仍是 VedAstro。
