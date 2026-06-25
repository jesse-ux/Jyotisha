# Antigravity AI Ayanamsa (岁差) 对齐与精度计划 (Round 28)

## 为什么需要对齐
Swiss Ephemeris (swisseph) 虽然精度极高，但 B.V. Raman 或 K.P. 等学派对 1900-2000 年间的 Ayanamsa 起点认定与 Lahiri (Chitra Paksha) 存在分歧。差 0.5 度就会导致分盘（尤其是 D60）出现颠覆性改变。

## 审计目标
1. 提取 JHora 中所有的 Ayanamsa 选项：True Chitra, Mean Chitra, Raman, Pushya, KP (Krishnamurti), Fagan/Bradley。
2. 我们目前 API 是通过调用 `flatlib` 底层 `swe.set_topo` 加上 offset。需要确认如何传递 Ayanamsa enum 给 `flatlib`。
3. 精度断言：在 1980, 2000, 2025 年的三个时间点，比较我们和 PyJHora 的 Ayanamsa 秒级差异。

## 状态
`部分成立`
