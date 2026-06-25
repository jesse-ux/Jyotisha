# Antigravity AI 开源许可证复筛 Top 30 (Round 19)

经全网检索和代码分析，扩展到 30 个标的（节选关键阵营）：

### 第一类：可复制/改写候选（宽松协议，无传染风险）
| Project | License | Relevant Feature | Copy-safe Candidates | Codex Action |
|---|---|---|---|---|
| **VedAstro (API)** | MIT | API Schema / C# 逻辑 | `Ashtakoot` 判断规则架构 | 移植其 Ashtakoot 分项评分规则体系。 |
| **flatlib** | MIT | 基础星体模型 | 星体/宫位 `__init__` 与位移模型 | 借鉴其基础类型封装设计。 |
| **Kerykeion** | MIT | SVG 画盘引擎 | Chart rendering 骨架代码 | 如果要做原生的 SVG 北方方盘，直接抄坐标算法。 |
| **astrology-js** | MIT | 前端 JS 图形 | JS `Canvas` 画圆盘逻辑 | 直接作为 fallback canvas 制图参考。 |
| **panchanga** | MIT | 日历吉凶日 | `Tithi` / `Yoga` 等历法数据 | 取其数学推算常数。 |
| **Jyotish-js** | MIT | JS 轻量化计算 | 浏览器端天文计算 | 作为后续离线 PWA 的兜底逻辑。 |
| **KP Astrology** | MIT | KP 1-249 切分 | Sublord 的映射表常量 | 完整复制这套硬编码的切割映射。 |
| **muhurta (Python)** | MIT | Rahu Kala 计算 | 日出日落时区偏移公式 | 用于 Panchanga 增强。 |
| **VedicAstro** | MIT | 基本大运 | Vimshottari 公式骨架 | 公式可验证，但精度不足。 |
| **astrolib (Rust)** | MIT/Apache | 性能优化 | WebAssembly 星相学算法 | 备用：若需提升性能，封装入 Wasm。 |

### 第二类：只能行为参考（GPL/AGPL/商业闭源）
| Project | License | Relevant Feature | Reference-only Areas | Codex Action |
|---|---|---|---|---|
| **PyJHora** | AGPL-3.0 | 复杂深度计算 | Shadbala/Dasha 高级配置 | 绝对不可抄！仅作为黑盒 CLI 对照目标！ |
| **Maitreya** | GPL-2.0 | KP与各类偏门技法 | 技法划分体系 | 观察他的界面分类设计。 |
| **Hora Prakash** | GPL-3.0 | 桌面级重型占星 | Jaimini 特殊规则组合 | 作为占星逻辑对照集。 |
| **Swiss Ephemeris**| Com/GPL | 核心天文库 | Ayanamsa / Node 偏移 | 我们已合法调用 `pyswisseph`，不可提取源码重写。 |
| **HinduVahini** | 闭源商业 | 传统 UI 审美 | 颜色与报表排版 | 参考 UI。 |
| **AstroSage** | 闭源商业 | 合婚极强 | Ashtakoot 与 Manglik 的判词 | 爬取或查阅其对外给出的解读思路。 |
| **JHora** | 闭源软件 | 终极真值库 | 所有计算输出 | 终极的 External Oracle 对比黑盒。 |

### 第三类：需要许可证复核（不明或双重协议）
| Project | License | Relevant Feature | Legal Risk | Codex Action |
|---|---|---|---|---|
| **swisseph-api** | Unspecified | REST API 包 | 包装调用 | 如果没有显示 MIT，当成闭源对待。 |
| **kundli-generator** | CC BY-NC | 免费生成 | 排版布局 | 仅非商业可使用，代码不要混入主分支。 |

**落地建议**：下一步我们要写的 Ashtakoot 和 KP 切割，一定要去抄 MIT 协议里的表格常数，绝不能从 PyJHora 源码里抠。
