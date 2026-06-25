# Antigravity AI 外部 Oracle 样本任务清单 Top 40 (Round 30)

## 人肉数据搜集蓝图

要让系统跑通黑盒测试，不要写代码，去以下网站截图并填入 `references/oracle/external_oracle_cases.json`！

| 领域 | 来源工具 | 样本特征 | 目标记录字段 |
|---|---|---|---|
| **夏令时边界** | AstroSage / JHora | 1984 年秋季加州出生。 | 必须记下确切的 UTC Offset，以及月亮所在的 Navamsha。 |
| **高阶分盘 (D60)** | JHora | 随机 3 个名人。 | 只看上升点 (Lagna) 落在哪个星座，D60 最吃微秒级差距。 |
| **Ashtakoot (合婚)** | AstroSage | 2 对明星夫妻，2 对普通人。 | 记下 Vashya, Nadi 等 8 项的单项浮点数，不能只记总分。 |
| **Kuja Dosha 豁免** | AstroSage | 命盘火星在 7 宫但旁边有木星。 | 记下平台是否判为 `Manglik Cancelled`。 |
| **Rahu Kala 极地**| Drik Panchang | 挪威特罗姆瑟，夏至日。 | 记下平台在没有日落时怎么算 Rahu Kala。 |
| **Chara Dasha** | JHora | 名人盘。 | 记下它前 5 步大运的跨度年份（有 7 星/8 星两种结果，记下 JHora 的偏好）。 |

## 状态
`需要人工外部工具`
