# Antigravity AI 全网开源项目许可证与可复用性矩阵 (Round 18)

| Project | URL/Search | License | Language | Relevant Features | Reusable Directly? | Copy-safe Candidates | Reference-only | Risks | Codex Action |
|---|---|---|---|---|---|---|---|---|---|
| **PyJHora** | /bivashy/pyjhora | AGPL-3.0 | Python | Dasha, Shadbala, Ashtakavarga | 🔴 否 | 无 | 算法参数、星体索引、测试集 | 传染性极强，代码绝不可抄。 | 仅用 CLI 输出验证。 |
| **VedAstro** | /VedAstro | MIT | C# / JS | API 服务, 库卡 | 🟢 是 | 前端交互、API schema | 底层算法 | 需要 C# 互操作转换。 | 提取前端呈现逻辑。 |
| **Swiss Ephemeris (js)**| /mivion/swisseph | GPL/Com. | JS | 天文底层 | 🔴 否 | 无 | Ayanamsa 常数 | 商业使用需买断许可。 | 继续使用 pyswisseph。 |
| **flatlib** | /flatlib | MIT | Python | 西洋占星基础 | 🟢 是 | 基础行星类封装 | 吠陀技法不支持 | 年代久远，缺乏吠陀。 | 可复用基本天文类。 |
| **Kerykeion** | /kerykeion | MIT | Python | 现代占星、图表 | 🟢 是 | 盘纸绘制、SVG | 仅支持西方行星属性 | SVG 制图逻辑可搬运。 | 参考绘制风格与代码。 |
| **astrology-js** | /astrology-js | MIT | JS | 前端星盘画图 | 🟢 是 | 圆盘绘画逻辑 | UI 太老旧 | 印度方盘需自己写。 | 搬运坐标旋转逻辑。 |
| **panchanga** | /sanskrit-prog/ | MIT | Python | 极高精度日历 | 🟢 是 | Tithi, Karana, Yoga | 大量梵文编码规则 | 依赖重，不易轻量化。 | 摘取核心天文算法。 |
| **Maitreya** | /maitreya | GPL-2.0 | C++ | 深度技法，K.P. | 🔴 否 | 无 | 界面布局、K.P.逻辑 | 协议传染，老旧 C++。 | 仅观察 KP 划分。 |
| **HinduVahini** | Web / App | 闭源 | N/A | 传统 UI、排版 | 🔴 否 | 无 | 产品排版流 | 闭源不可碰。 | UI 竞品分析。 |
| **AstroSage** | Web / App | 闭源 | N/A | 最强合婚、运势 | 🔴 否 | 无 | Ashtakoot 指标维度 | 闭源不可碰。 | 对标合婚指标清单。 |
| **Jyotish-js** | /jyotish-js | MIT | JS | 简易吠陀排盘 | 🟢 是 | JS 端的坐标推算 | 缺少深层 Yoga/Dasha | 长期未维护。 | 备用前端计算兜底。 |
| **VedicAstro** | /vedic-astro | MIT | Python | Dasha, 宫位计算 | 🟢 是 | Vimshottari 基础算法 | 计算精度极低 | 无法过 BPHS 测试。 | 只能当玩具看。 |
| **Hora Prakash** | /horaprakash | GPL-3.0 | C++ | 桌面端重型 | 🔴 否 | 无 | Jaimini 规则细节 | 传染。 | 算法对标。 |
| **KP Astrology** | /kp-astro | MIT | JS | KP Sublord | 🟢 是 | Sublord 切片表 | KP Ayanamsa offset | KP 特定规则。 | 移植 Sublord 常数表。 |
| **Muhurta Calc** | /muhurta | MIT | Python | 吉凶时计算 | 🟢 是 | Rahu Kala 计算 | 缺乏综合评判 | 时区依赖高。 | 复用日出日落逻辑。 |

### 总结
- **可直接复制/改写的宽松许可证**：VedAstro (UI 层), flatlib, Kerykeion, panchanga, KP Astrology。
- **只能学习行为不能复制**：PyJHora, Swiss Ephemeris 核心源码, Maitreya, Hora Prakash。
