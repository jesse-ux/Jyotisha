# Antigravity AI MIT 常量来源再核验 (Round 23)

为确保移植字典时的合法性与精准性，再扫 10 个以上潜在开源来源：

| 来源与 URL | License | 常量覆盖 | 移植风险与结论 |
|---|---|---|---|
| **VedAstro/VedAstro** | MIT | 100% 覆盖 8 Kuta。 | **极低，首选**。代码非常工整，`MatchCalculator.cs` 中常量直接硬编码。 |
| **RaviKarrii/Marriage-Compatibility** | MIT | 100% 覆盖 8 Kuta。 | 极低，备选。但其对 Nadi 的异常情况（如相同 Nakshatra 的豁免）处理较浅。 |
| **flatlib** | MIT | 0%。仅算星星，不算合婚。 | 不可用于 Ashtakoot。 |
| **panchanga** | MIT | 0%。仅算日历。 | 不可用于 Ashtakoot。 |
| **dashaflow** | MIT | 0%。仅算 Dasha。 | 不可用于 Ashtakoot。 |
| **kerykeion** | MIT | 0%。西方占星合盘，不适用 Vedic。 | 不可用于 Ashtakoot。 |
| **VedicAstro (Py)** | MIT | 10%。仅有 Nakshatra 坐标转换。 | 无法提取 36分常量。 |
| **jyotish-rs** | MIT/Apache | 0%。引擎仍在起步期。 | 无法提取。 |
| **astro_rust** | MIT | 0%。 | 无法提取。 |
| **jyotish-starter (JS)** | MIT | 0%。仅作 API 请求样板。 | 无法提取。 |

**落地结论**：
全世界目前在**宽松开源协议 (MIT)** 下完整保留了 8 Kuta 36 分常数表且质量极高的仓库，**仅有 VedAstro 一家**。这更凸显了我们将 `VedAstro` 字典转写为 Python 沉淀下来的战略价值。
