# Antigravity AI Panchang / Muhurta 缺口与对标优先级 (Round 25)

印度占星应用在商业上最大的日活（DAU）留存点是日历（Panchang），而非复杂的出生排盘。

| 核心组件 | 商业应用提供状态 | 本项目现状 | 实现优先级 |
|---|---|---|---|
| 1. Tithi (日月相位度数差/12) | 首页大字显示 | 完全没有 | **P0** |
| 2. Karana (半个 Tithi) | 伴随显示 | 完全没有 | **P1** |
| 3. Nakshatra (每日月亮驻扎) | 每日运势基石 | 只有排盘时有 | **P0** |
| 4. Yoga (日月合成距离) | Panchang 五要素 | 完全没有 | **P1** |
| 5. Vara (星期主星) | 简单 | 完全没有 | **P2** |
| 6. Rahu Kalam (每日凶时) | 极受南印欢迎 | 完全没有 | **P0** (必须做) |
| 7. Yama Gandam (凶时) | 伴随显示 | 完全没有 | P2 |
| 8. Muhurta 择吉引擎 | 收费项目 | 完全没有 | P3 (太遥远) |

**实现结论**：要想让应用不仅是用来“排一次盘就走”的工具，必须实现当日 Panchang 查询。
**副手下一轮任务**：提取 `panchanga` (MIT) 库或 `VedAstro` 库中关于 Rahu Kalam 时间段推算的常数公式。
**Codex 可做任务**：创建一个 `scripts/panchang.py`，写死 5 个空函数骨架。
**Codex 可做任务 2**：在 `panchang.py` 里优先把 Tithi 的除法公式（ `(Moon - Sun) % 360 / 12` ）实现。
