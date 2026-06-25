# Antigravity AI VedAstro 深入复用审计 (Round 21)

| 审计维度 | 调查结果 |
|---|---|
| 1. License 确认 | **MIT License**，极为宽松，支持商用与修改。 |
| 2. 是否 MIT 覆盖目标 | 是的，`MatchChecker.cs` 等文件都在 MIT 授权下。 |
| 3. Match Checker 入口 | 包含 `MatchCalculator.cs`，可以直接提取其 36 分评判表。 |
| 4. 8 Kuta / 10 Kuta | 它支持标准的 8 Kuta (Ashtakoot) 算法，且结构清晰。 |
| 5. 是否有常量表 | 🔴 虽然有，但嵌在 C# 的强类型对象 `Constellation` 里面，需要写个脚本清洗为 JSON。 |
| 6. 是否依赖底层星历 | 它依赖 Swiss Ephemeris，但我们不需要抄它的星历计算，只抄**打分对照表**即可！ |
| 7. C# 移植成本 | 🟡 比较低。用正则表达式或者大模型直接把它 C# 文件里的星宿矩阵改成 Python Dict。 |
| 8. Attribution 要求 | MIT 要求保留原作者版权声明（Copyright）。 |
| 9. 可复制最小文件 | 提取其中关于 Nadi/Gana 的 27x27 星宿分数矩阵表。 |
| 10. 不应复制的依赖 | 绝对不复制它的 API 服务器架构和 UI。 |
| 11. 与本仓库差异 | 我们目前的 `ashtakoot.py` 是空壳算法，没有具体的打分字典，VedAstro 正好补全了字典。 |
| 12. 是否进入 Round 22 | 🟢 **强烈推荐**。这是补齐合婚算法的捷径。 |

**最小 Codex 改动建议**：写一段 python 脚本从 VedAstro 摘取 Ashtakoot 常数。但先需要在文件顶部加上 `Copyright (c) VedAstro` 声明。
