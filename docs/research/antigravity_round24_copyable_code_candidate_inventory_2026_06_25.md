# Antigravity AI 可复制开源代码候选名录 (Round 24)

依据“仅限 MIT/Apache-2.0/BSD/ISC/CC0”的铁律，为您筛选如下“零污染”宝库：

| 项目与 URL | License 证据 | 可复制模块 | 对应缺口 | 移植成本 | 不可复制项 |
|---|---|---|---|---|---|
| **VedAstro/VedAstro** | MIT (仓库根目录 LICENSE) | `MatchCalculator.cs` 中硬编码的 Varna, Vashya, Tara, Yoni 数组与 switch/case。 | Ashtakoot 36分全部常数。 | 高 (需 C# 到 Python 手工/正则翻译)。 | 它的 HTTP/UI 层太庞大，只取算法。 |
| **panchanga** (sanatana/panchanga) | MIT | `jyotisha/panchaanga/spatio_temporal/` 里的 `tithi.py`, `karana.py` | 补全完全缺失的印度老黄历 (Panchang) 5 大支柱。 | 中 (依赖了不同的底层库，需适配我们的 flatlib 底盘)。 | 那些关于节日节气的过度庞大 JSON，我们不需要。 |
| **flatlib** | MIT | `flatlib/ephem/` 下的恒星时推算。 | 用作我们岁差算法的兜底参照。 | 极低 (已用作底层生态)。 | 所有的西方占星概念 (如 Placidus 宫位)。 |
| **RaviKarrii/Marriage** | MIT | `src/.../Kuta.java` | 若 VedAstro 有些边角没读懂，用此 Java 代码做交叉比对。 | 中。 | 无。 |
| **jyotish-starter** | MIT | 它的 API Request 包装。 | 对接给别人用时的 SDK 样例。 | 极低。 | 它里面没有真核算法。 |

**不可复制补充说明**：
即便是在 Github 上搜到的一段野鸡 `calculate_dasha.py`，只要它没附带明确的 MIT 许可，默认按照 GitHub 霸王条款属于原作者版权，一律**不可照抄**。

**副手下一轮任务**：编写一份 Python 脚本，以正则表达式解析 VedAstro 的 `MatchCalculator.cs` 原文并自动转为 Dict 字符串。
**Codex 可做任务**：根据上面的名录，放心大胆地抄写 VedAstro 的常数，它是我们在合婚模块的唯一生路。
