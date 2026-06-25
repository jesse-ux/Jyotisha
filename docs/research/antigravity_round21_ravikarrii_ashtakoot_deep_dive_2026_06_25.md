# Antigravity AI RaviKarrii Ashtakoot 深度审计 (Round 21)

| 审计维度 | 调查结果 |
|---|---|
| 1. License 确认 | **MIT License**。 |
| 2. 完整 REST API | 是的，该仓库是一个 Spring Boot 项目。 |
| 3. Kuta 常量表 | 🟡 包含。存在于 Java 枚举和预设数组中。 |
| 4. Nakshatra 映射 | 包含 27 星宿到各属性（如 Nadi）的映射。 |
| 5. 输入模型 | 接收男女双方的 Nakshatra 和 Pada。 |
| 6. 输出模型 | 输出一个带有 8 项得分和总分的 JSON。 |
| 7. Java 移植成本 | 🟡 中等。其代码较为过程化，提取字典不如 VedAstro 清晰。 |
| 8. 测试样本 | 包含了一些基础的单元测试。 |
| 9. 与现有算法差距 | 它实现了具体的计分规则，但缺少 Kuja Dosha 和行星位置相关的深层豁免逻辑。 |
| 10. 可复制文件 | 提取其 Nakshatra 属性表。 |
| 11. Attribution 方式 | 在 `ashtakoot_constants.py` 头部增加版权声明。 |
| 12. 优先于 VedAstro？| 🔴 **否**。VedAstro 的维护度更高，包含更权威的异常处理和容错。优先用 VedAstro。 |

**最小 Codex 改动建议**：作为备用参考库。如果 VedAstro 的某个 Nadi 逻辑看不懂，可以用这个 Java 库的代码作为对照辅导。
