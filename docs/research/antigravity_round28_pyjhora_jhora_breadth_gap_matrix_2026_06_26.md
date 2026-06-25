# Antigravity AI PyJHora/JHora 技法广度差距表 (Round 28)

## 技法差距分类

| 技法名称 | 在本项目中的状态 | PyJHora/JHora 中的状态 | 追赶建议 |
|---|---|---|---|
| Vimshottari Dasha | 已有且可见 | 极度细化到 Prana Dasha | 下钻到第五级大运。 |
| Ashtottari Dasha | 未登记新技法 | 支持 | 新增计算模块。 |
| Yogini Dasha | 未登记新技法 | 支持 | 新增计算模块。 |
| Kalachakra Dasha | 未登记新技法 | 支持 | 新增计算模块，这是进阶大运的核心。 |
| Jaimini Chara Dasha | 已有但隐藏 | 支持，且有多种变体 | 暴露 API 并解决不同学者的排盘分歧。 |
| Narayana Dasha | 未登记新技法 | 支持 | 新增计算模块。 |
| Shadbala - Sthana | 已有且可见 | 高度精细 | 继续对齐各子项 Rupa 值。 |
| Shadbala - Ishta/Kashta | 未登记新技法 | 支持 | 加入吉凶力量量化。 |
| Bhava Bala (宫位力量) | 未登记新技法 | 支持 | 新增宫位强弱模块。 |
| Ashtakavarga 细节 | 已有但隐藏 | 详尽展示 Kakshya | 在前端或 CLI 铺开细致的 12 宫打分。 |
| Special Lagnas | 已有但隐藏 | 包含 Hora, Ghati 等 | 把各种特殊上升点加入 `/api/chart` 暴露。 |
| Naisargika Karaka | 已有但未校准 | 完备 | 与 JHora 常数对齐。 |
| Choghadiya / Hora | 已有但隐藏 | 完备 | 加入 Panchanga UI。 |
| Eclipse (日/月食) | 未登记新技法 | 完备 | 依托 Swiss Ephemeris 很快能加。 |
| Tithi Pravesha (年度) | 未登记新技法 | 完备 | 与 Tajika 并列的年运预测。 |

## 分析
差距主要在**长尾 Dasha** 以及 **细分力量体系 (Bhava Bala, Vimsopaka)** 上。PyJHora 因其 AGPL 属性只能作为黑盒靶标（benchmark_only）。

## 状态
`已成立`
