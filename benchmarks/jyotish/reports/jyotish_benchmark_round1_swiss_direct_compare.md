# Jyotish benchmark 第一轮 Swiss direct 对比报告

生成时间：2026-06-03

## 1. 范围

- 对比对象：当前 skill canonical baseline vs 直接调用 Swiss Ephemeris。
- 配置：Sidereal Lahiri，Mean Node，行星黄经与 Nakshatra 字段。
- 本轮不比较上升、宫位、D9/D10、大运；这些留给下一轮多引擎/参数冻结测试。

## 2. 总体结果

- 字段总数：450
- 匹配：450
- 不匹配：0
- 匹配率：100.00%

## 3. 分字段结果

| Field | Total | Match | Mismatch |
|---|---:|---:|---:|
| degree_in_sign | 90 | 90 | 0 |
| nakshatra | 90 | 90 | 0 |
| nakshatra_pada | 90 | 90 | 0 |
| retrograde | 90 | 90 | 0 |
| sign | 90 | 90 | 0 |

## 5. 解释

- 若 sign/nakshatra 大量一致，说明当前 skill 的核心 Lahiri 行星计算大方向可信。
- 若 degree_in_sign 出现系统性差异，优先检查 ayanamsa、True/Mean Node、UTC换算、Swiss flags。
- 本轮发现的问题只约束计算层，不直接评价解释和预测能力。