# Jyotish benchmark 第二轮 Swiss extended 对比报告

生成时间：2026-06-03

## 1. 范围

- 对比对象：当前 skill canonical baseline vs 直接调用 Swiss Ephemeris + 独立复写的 D9/D10/Vimshottari 公式。
- 样本：10 个公开/虚构 smoke case，不含用户个人资料。
- 本轮新增字段：Ascendant、D9、D10、当前 Vimshottari MD/AD。
- 注意：D9/D10/Vimshottari 的公式仍参考当前 skill 的公开公式重写，属于“独立脚本复算”，不是 PyJHora/JHora 级别的完全外部流派验证。

## 2. 总体结果

- 字段总数：490
- 匹配：486
- 不匹配：0
- 边界敏感：4
- 不可比：0
- 严格匹配率：99.18%
- 容差/边界归因后可接受率：100.00%

## 3. 分模块结果

| Section | Total | Match | Mismatch | Boundary sensitive | Not comparable |
|---|---:|---:|---:|---:|---:|
| D10 | 200 | 196 | 0 | 4 | 0 |
| D9 | 200 | 200 | 0 | 0 | 0 |
| ascendant | 30 | 30 | 0 | 0 | 0 |
| dasha | 60 | 60 | 0 | 0 | 0 |

## 4b. 边界敏感字段

- 这些字段不是普通错配，而是度数处于分盘切分边界附近；四舍五入、Mean/True Node、JHora流派参数都可能导致落入相邻分盘。后续必须用 PyJHora/JHora 再仲裁。

| Sample | Section | Body | Field | Local skill | Swiss extended | Delta |
|---|---|---|---|---|---|---:|
| smoke_tokyo_1964_noon | D10 | Rahu | sign | Gemini | Cancer |  |
| smoke_tokyo_1964_noon | D10 | Rahu | degree_in_sign | 29.9773 | 0.0278 | 29.9495 |
| smoke_tokyo_1964_noon | D10 | Ketu | sign | Sagittarius | Capricorn |  |
| smoke_tokyo_1964_noon | D10 | Ketu | degree_in_sign | 29.9773 | 0.0278 | 29.9495 |

## 5. 判断

- 第二轮未发现不匹配，说明当前 skill 的 Ascendant、D9、D10、Vimshottari 当前 MD/AD 在本地独立复算下稳定。
- 这仍然不能替代 PyJHora / JHora / VedAstro 的外部多引擎验证；它只是把内部公式错误和 UTC/边界错误的风险进一步压低。