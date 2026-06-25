# Antigravity AI 高阶技法优先级矩阵 (Round 13)

在我们拥有了一个异常透明和严苛的核对底座之后，后续精度的战争将转向具体的高阶技法覆盖。依照 JHora、PyJHora 与 VedAstro 的标尺，以下是我们的下一批攻坚优先级：

| 优先级 | 技法 | 为什么影响准确率 | 推荐验证方式 | 涉及文件 |
|---|---|---|---|---|
| **#1** | **Shadbala 六分量** | 目前系统只提供了全览力量估算。在高级断命时，无法分辨星体力量究竟是来源于方位（Dig Bala）还是状态（Sthana Bala），这使得精准择日成了碰运气。 | JHora / PyJHora 黑盒数字截屏核对 | `jyotish-app/main.js`, 核心引擎 Shadbala 计算模块 |
| **#2** | **Vimshottari Dasha 边界日期** | 即便是 0.1 度的月亮经度偏差（约合 6 角分），放大到 120 年寿命尺度下，大运起点都会产生数十天的漂移。目前的边界日期粗粒度在遇到关键节点换运时极易翻车。 | JHora 真值采集表（我们目前的 5 个待处理模板中有 3 个与此有关） | 核心大运推演模块, `oracle_cases.json` |
| **#3** | **Koota 合婚 (Ashtakoot / Porutham)** | 很多入门产品通过 36 分系统吸引海量用户。我们目前只有基础的落座和星象，如果缺乏 Koota 匹配模型，将失去极大的一块占星日常需求。 | VedAstro 的开放 API 或对照开源合婚系统 | 需建立全新的 `koota_matching.py` 并接入 App |
| **#4** | **KP Prashna / Sub Lord** | KP（Krishnamurti Paddhati）系统的核心在黄道十分精细的切分（Sub Lord 甚至 Sub Sub Lord）。这是所有高端择时玩家的标配，我们目前处于盲区。 | VedAstro 极其完善的 KP API 对标 | `jyotish-app/jyotish-advanced.js`, KP 独立模块 |

此矩阵将指导我们在解锁了全局缩放（`production_tuning_allowed`）之后，把火力倾泻到何处。
