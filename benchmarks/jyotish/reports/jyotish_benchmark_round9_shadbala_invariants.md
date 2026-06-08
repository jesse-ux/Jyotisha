# Jyotish benchmark 第九轮 Shadbala 内部不变量报告

生成时间：2026-06-04

## 1. 范围

- 样本：10个公开/虚构 smoke case，不包含真实用户个人资料。
- 对比对象：`shadbala` 子命令与 `full-reading.modules.shadbala`。
- 验证类型：结构完整性、六重力量组件范围、总分公式、Rupa/Virupa换算、排名一致性、full-reading输出一致性。
- 重要边界：本轮不是外部软件绝对值对标；当前本地未找到稳定可用的完整 Shadbala 外部基准，因此只能证明内部一致性，不能证明传统公式完全一致。

## 2. 总体结果

- 检查总数：1200
- 通过：1200
- 失败：0
- 通过率：100.00%

## 3. 分检查项结果

| Check | Total | Match | Mismatch |
|---|---:|---:|---:|
| chesta_bala_range | 70 | 70 | 0 |
| dig_bala_range | 70 | 70 | 0 |
| drik_bala_range | 70 | 70 | 0 |
| full_reading_rank_match | 70 | 70 | 0 |
| full_reading_total_match | 70 | 70 | 0 |
| full_reading_total_min_required | 10 | 10 | 0 |
| full_reading_total_shadbala | 10 | 10 | 0 |
| ishta_pct_formula | 70 | 70 | 0 |
| kala.total_range | 70 | 70 | 0 |
| method_present | 10 | 10 | 0 |
| min_required_constant | 70 | 70 | 0 |
| naisargika_constant | 70 | 70 | 0 |
| ranking_permutation | 10 | 10 | 0 |
| ranking_sorted_by_total | 10 | 10 | 0 |
| required_fields | 70 | 70 | 0 |
| seven_planets_present | 10 | 10 | 0 |
| sthana.drekkana_enum | 70 | 70 | 0 |
| sthana.kendra_enum | 70 | 70 | 0 |
| sthana.ojayugma_enum | 70 | 70 | 0 |
| sthana.ucha_bala_range | 70 | 70 | 0 |
| strongest_matches_rank | 10 | 10 | 0 |
| total_rupas_conversion | 70 | 70 | 0 |
| total_virupas_sum | 70 | 70 | 0 |
| weakest_matches_rank | 10 | 10 | 0 |

## 5. 结论

- Shadbala 输出结构、总分聚合、Rupa/Virupa换算、排名、full-reading一致性均通过内部不变量验证。
- 但源码仍包含简化项：Nathonnata Bala 二值化、部分 Saptavargaja 子分盘近似、Chesta Bala 速度分档近似、Drik Bala 简化相位权重。
- 因此能力标注应从 `covered` 降级为 `partial`：可作为内部一致的强弱参考，不应声称已完成传统 Parashara Shadbala 的外部绝对值校准。