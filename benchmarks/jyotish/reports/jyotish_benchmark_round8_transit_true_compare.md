# Jyotish benchmark 第八轮 Transit 真实过境对比报告

生成时间：2026-06-03

## 1. 范围

- 对比对象：full-reading.modules.transit_positions / transit_multi_reference vs 直接调用 Swiss Ephemeris。
- 样本：10个公开/虚构 smoke case，不包含真实用户个人资料。
- 配置：Sidereal Lahiri，Mean Node，transit date 使用样本 today 字段。
- 重点：确认 full-reading 的多参考点 Transit 不再使用 natal positions fallback，而是使用真实过境行星位置。

## 2. 总体结果

- 字段总数：340
- 匹配：340
- 不匹配：0
- 匹配率：100.00%

## 3. 分字段结果

| Field | Total | Match | Mismatch |
|---|---:|---:|---:|
| transit_multi_reference.data_layer | 10 | 10 | 0 |
| transit_multi_reference.sign | 40 | 40 | 0 |
| transit_multi_reference.target_date | 10 | 10 | 0 |
| transit_positions.data_layer | 10 | 10 | 0 |
| transit_positions.degree_in_sign | 90 | 90 | 0 |
| transit_positions.retrograde | 90 | 90 | 0 |
| transit_positions.sign | 90 | 90 | 0 |

## 5. 结论

- full-reading 的 Transit 输出已明确使用 true_transit_positions。
- transit_positions 与 Swiss direct 完全对齐；transit_multi_reference 的 Jupiter/Saturn/Rahu/Ketu 星座也与真实过境一致。