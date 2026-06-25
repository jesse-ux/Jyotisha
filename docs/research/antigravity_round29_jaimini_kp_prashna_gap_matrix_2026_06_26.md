# Antigravity AI Jaimini / KP / Prashna 缺口总表 (Round 29)

## 进阶门派的冰山一角

| 门派 | 核心技能 | 当前状态 | 缺口 |
|---|---|---|---|
| **Jaimini** | Chara Karakas (灵魂标记星) | `部分成立` | JSON 里有，前端没展示。缺 7/8 星方案切换。 |
| Jaimini | Padas (Arudha) | `未成立` | 算 AL (Arudha Lagna) 的逻辑在 `dashaflow` 里有，我们还没集成。 |
| Jaimini | Chara Dasha (大运) | `部分成立` | 后端算好了，API 没接。 |
| **KP** | Placidus 宫位 | `未成立` | 我们底层强绑定了 Whole Sign。KP 必须用 Placidus 分割 12 宫。 |
| KP | 1-249 Sublord | `未成立` | 库里有个 CSV，但查表逻辑没整合到主轴 `jyotish_engine.py` 里。 |
| KP | Significators (代表星) | `未成立` | 根据行星在 Nakshatra 上的主星判定 A,B,C,D 级代表力。 |
| **Prashna** | 实时起卦功能 | `未成立` | 前端没有“当前时间立盘”的快捷键，要求用户填当前分秒太反人类。 |
| Prashna | 占星师时区锁定 | `未成立` | 卜卦看的是占星师本地时间，不是求问人时间。需要一个分离的时区设计。 |

## 状态
`部分成立`
