# Vedic Astrology 开源技法补课调研（2026-06-13）

> 来源：本地工作区 `vedic-astrology-open-source-research.md` 摘要，已在 v6.9.14 前后吸收到主仓库实施路线。

## 核心发现

| 技法 | 最完整开源参考 | 许可证 | 对 yinduzhanxing 的处理 |
|------|----------------|--------|-------------------------|
| Bhava Chalit | PyJHora `charts.py`/`house.py`，PanchangaAPI 端点，kundli-app JS | PyJHora AGPL；PanchangaAPI MIT-0 但源码不可见；kundli-app 未声明/GPL 依赖 | 不能复制 AGPL；v6.9.13 自研实现 Sripati/Porphyry/Equal/Whole Sign/Placidus/Koch + 行星重分配 |
| Sudarshana Chakra | PyJHora `sudharsana_chakra.py` | AGPL-3.0 | 不能复制 AGPL；v6.9.14 自研 Asc/Moon/Sun 三参考点盘 + 宫位收敛评分 |
| Varshaphala / Solar Return | PyJHora `tajaka.py`/`annual.py`；vedic-calc | PyJHora/vedic-calc AGPL；PanchangaAPI MIT-0 端点 | 保留为下一阶段外部校准目标，避免直接复制 AGPL |
| Tajika | PyJHora `tajaka_yoga.py`；vedic-calc | AGPL | v6.9.12 已补 10 种 Tajika Yoga，后续需和外部案例对照 |
| D60+ / 自定义分盘 | PyJHora D81/D108/D144/D150/D300 + Dm×Dn + D1-D300 | AGPL | v6.9.12 自研 D2/D3 变体、复合 D-m×n、自定义 D-N(2-300) |

## 许可证决策

- PyJHora / vedic-calc / Maitreya / kunjara 等 AGPL/GPL 项目只能用于算法理解和对照，不直接复制代码。
- MIT / MIT-0 项目可优先复用；源码不可见的 API 只能作为功能口径参考。
- 当前仓库保持 MIT 开源路线，避免引入 GPL/AGPL 传染性代码。

## 已吸收结果

- Bhava Chalit：从“整宫适配/partial”升级为完整不等宫位重分配。
- Sudarshana Chakra：从“D1×D9×D10 替代验证”升级为传统三参考点分析。
- 分盘：从 D1-D144 扩展到 D2/D3 变体、复合分盘、自定义 D-N(2-300)。
- 精度仪表盘已记录：非社区维度评分约 8.1/10；最大剩余缺口转为 Chara Dasha 解读层与 Vimshottari 细分应期。
