# Yogi / 上升度数 / 紧密合相财富专题冻结执行手册

> 来源：`references/yogi-avayogi-system.md`、`scripts/aspects.py`、`scripts/special_lagnas.py`、`4印度占星.docx`，并参考 Komilla Sutton 对 Personal Panchanga / Yogi Point 的公开说明
>
> **来源标签**: 【Panchanga传统 + 现代实践 + Skill执行冻结】 — Yogi/Ava Yogi 财富激活与紧密度数判断
>
> **版本**：v1.0 | **最后更新**：2026-06-26

---

## 0. 来源等级与使用原则

本手册采用“分层信任”，不能把网上文章或个案断语直接视为权威规则。

### A级：Panchanga / Nitya Yoga 基础

- `Yogi Point` 来自 Panchanga 的 `Nitya Yoga`，即太阳和月亮的关系。
- `Yogi planet` 是 Yogi Point 所在 Nakshatra 的主星。
- `Duplicate Yogi` 是该点所在 Rashi 的主星。
- `Avayogi` 是从 Yogi Nakshatra 起算第 6 个 Nakshatra 的主星。

Komilla Sutton 的 Personal Panchanga 文章明确把 Yogi planet / Yogi Point 放在 Panchanga 体系下，并提醒这些指标是**补充信息**，不能脱离本命盘主判断。

### B级：现代 Jyotish 实践，可作为强参考

- Yogi planet 与好运、繁荣、支持者有关。
- Avayogi 与阻碍、消耗、负反馈有关。
- Benefics 过境 Yogi Point 时，常被视为积极窗口。
- 伴侣或合作方的上升主若对应自己的 Yogi / Avayogi，可作为关系或财务互动的辅助线索。

### C级：网上文章/案例转述，只能作为线索

- “Yogi 点与上升点同 Nakshatra 必富”
- “Yogi 点与上升度数紧密合相必然成为富豪”
- “佩戴某宝石必激活财富”
- 名人案例中的财富断语

这些只能进入模板层，不能单独变成硬断语。

### 使用原则

1. 先看 Dhana Yoga / 2宫 / 11宫 / 9宫 / 5宫 / Lagna lord / D2 / D9 / D10。
2. 再用 Yogi / Avayogi 做财富激活与阻碍细化。
3. 紧密合相 `<1°` 只能提高置信度，不能替代财富承诺。
4. 宝石与补救必须保守表达，不可保证财富结果。

---

## 1. 用途

本手册把 `Yogi / Ava Yogi / Duplicate Yogi`、上升点度数、紧密合相、财富 Yoga 组合，冻结成一个可稳定执行的财富专题模板。

适用场景：

1. 用户问财富来源、财运爆发点、赚钱方向
2. 用户问“为什么某段时间突然有钱/破财”
3. 用户问合作对象、伴侣、环境是否激活财务
4. 用户问宝石、活动、行业是否适合自己
5. 用户盘中有上升点、Yogi 点、2/11 主星或财富星的紧密合相

---

## 2. 当前冻结边界

### 已冻结

1. `references/yogi-avayogi-system.md` 已有 Yogi / Ava Yogi / Duplicate Yogi 体系
2. `scripts/aspects.py` 已有 orb 与紧密相位基础
3. `scripts/special_lagnas.py` 已有 Hora Lagna、Ghati Lagna、Arudha 等特殊上升点
4. `generate_yoga_rules.py` 已有 Dhana Yoga / Lakshmi Yoga 等财富规则
5. `full-reading` 已能输出财富相关模块与证据

### 尚未完全冻结

1. Yogi Point 与 Lagna degree 的自动 `<1°` 检测
2. Yogi Point 与 2宫主 / 11宫主 / Jupiter / Venus 的紧密合相专题
3. Avayogi 与财富宫/财富星紧密关联的破财模板
4. Ashwini / Abhijit 等 Nakshatra 财富/天赋细节专题
5. 外部案例 benchmark

结论：

> 当前可以把 Yogi 财富体系作为“财富激活/阻碍的细化层”，但不能替代传统财富承诺判断。

---

## 3. 强制执行顺序

### Step 1. 先确认财富承诺

必须先看：

- 2宫、11宫、5宫、9宫
- 2宫主、11宫主
- Jupiter / Venus
- Lagna lord
- Dhana Yoga / Lakshmi Yoga
- D2 Hora
- D9 / D10 支持

若这些没有支持，Yogi 信号只能作弱提示。

### Step 2. 计算 Yogi 三元组

输出：

- Yogi Point
- Yogi planet
- Duplicate Yogi
- Avayogi planet
- Yogi Point 所在 Nakshatra / Rashi / House

### Step 3. 判断 Yogi planet 状态

必须看：

- 宫位
- 尊贵度
- 是否燃烧
- 是否逆行
- 是否受凶星严重影响
- 是否与财富宫主、财富星、Dhana Yoga 有联系

### Step 4. 检查 Avayogi 风险

必须看：

- Avayogi 是否落入 2/11/5/9/10
- Avayogi 是否合相财富宫主
- Avayogi 是否参与 Dasha
- Avayogi 是否与 Yogi / Duplicate Yogi 混杂

### Step 5. 检查紧密度数

优先检查 `<1°`：

- Lagna degree ↔ Yogi Point
- Yogi Point ↔ Jupiter / Venus
- Yogi Point ↔ 2宫主 / 11宫主 / 9宫主 / 5宫主
- Yogi Point ↔ Hora Lagna
- Avayogi ↔ 2宫主 / 11宫主 / Lagna lord

说明：

> `<1°` 是强放大器，不是独立承诺。若没有财富承诺，它只说明该主题敏感，不保证财富结果。

---

## 4. 财富信号分级

### 低置信财富提示

条件：

- 只有 Yogi planet 强
- 或 Yogi Point 位于吉宫
- 但 Dhana Yoga / D2 / Dasha 不支持

输出：

- “这是一条可利用的好运方向”
- “更像潜力，不是已兑现财富承诺”

### 中置信财富信号

条件满足两项以上：

- Yogi planet 强
- Yogi Point 位于 2/5/9/10/11
- Yogi planet 与 2/11 主星有关
- Dasha 激活 Yogi / Duplicate Yogi
- Jupiter 过境 Yogi Point 所在 Nakshatra

输出：

- “财富机会更容易通过某领域出现”
- “适合顺势做相关行业/活动/合作”

### 高置信财富窗口

必须同时满足：

1. D1 财富承诺存在
2. D2/D9/D10 至少一层支持
3. Yogi planet 或 Yogi Point 与财富链强关联
4. Dasha / Transit 同步激活
5. Avayogi 没有严重破坏，或破坏被明确化解

输出：

- “高优先级财富窗口”
- “适合执行具体财务行动，但仍需现实风控”

---

## 5. 上升点与 Yogi Point

### 同 Nakshatra

可以说：

- 出生人格与 Yogi Point 的繁荣方向同频
- 此人更容易把个人行动与好运方向连接
- 若财富承诺也强，可提高财富兑现置信度

不可以说：

- 必富
- 一定成为富豪
- 不需要 Dasha/现实行动也能发财

### `<1°` 紧密合相

可以说：

- Yogi Point 对自我、身体、人生方向的影响极敏感
- 该人更容易在对应 Nakshatra/Rashi/House 主题上被激活

不可以说：

- 单凭此项断巨富

---

## 6. Avayogi 风险模板

### Avayogi 连接财富宫

允许输出：

- 财富主题容易伴随代价、延迟、反复或错误判断
- 需要更严格风险管理

### Avayogi 连接 Lagna / Lagna lord

允许输出：

- 本人决策模式容易把阻碍带入财务
- 需要避免 Avayogi 所象征的人、行业或行为模式

### Avayogi Dasha

允许输出：

- 该运期需保守财务策略
- 若同时有强 Yogi / Dhana Yoga 支持，可能表现为“压力中带机会”

禁止输出：

- 一定破财
- 一定失败

---

## 7. 与其他财富系统的硬联动

### 与 Dhana Yoga / Lakshmi Yoga

- Dhana Yoga 给出财富承诺
- Yogi Point 给出激活路径
- 两者同向时，才可提高财富判断强度

### 与 Dasha

- Yogi / Duplicate Yogi Dasha：机会增加
- Avayogi Dasha：阻碍增加
- 混合运：好坏交织，必须看 Antar / Transit

### 与 Transit

- Jupiter 过境 Yogi Point：较积极
- Venus 过境 Yogi Point：资源/关系/美感机会
- Saturn 过境 Yogi Point：考验、延迟、结构化机会
- Rahu 过境 Yogi Point：突然、非传统、高波动

### 与 D2 / D9 / D10

- D2 确认财富积累能力
- D9 确认福德与长期稳定
- D10 确认事业渠道

---

## 8. 行动建议模板

可建议：

- 选择 Yogi planet 象征的行业/活动
- 在 Yogi Dasha / Jupiter transit 期间主动推进财务计划
- 避开 Avayogi 过强时的大额冒险
- 结合现实财务管理，不做孤注一掷

不可建议：

- 保证收益
- 用宝石替代理性财务决策
- 因某点位而鼓励赌博、投机或高风险行为

---

## 9. 工业化字段骨架

后续模板化建议字段：

- `yogi_point_longitude`
- `yogi_point_nakshatra`
- `yogi_point_house`
- `yogi_planet`
- `duplicate_yogi`
- `avayogi`
- `lagna_yogi_distance_deg`
- `tight_orb_hits`
- `wealth_lord_links`
- `dhana_yoga_support`
- `d2_support`
- `d9_support`
- `d10_support`
- `dasha_activation`
- `transit_activation`
- `confidence`
- `narrative_short`
- `narrative_deep`
- `boundary_note`

---

## 10. 最短执行卡

如果时间很紧，至少执行：

1. 先判断 D1 财富承诺
2. 看 D2 / D9 / D10 是否支持
3. 算 Yogi Point / Yogi / Duplicate Yogi / Avayogi
4. 看 Yogi planet 是否强
5. 查 `<1°` 紧密合相
6. 查 Dasha / Transit 是否激活
7. 输出置信度与边界

只做到前 5 步，叫**财富潜力定位**。
做到第 7 步，才叫**财富窗口判断**。

---

## 11. 结论

Yogi / Avayogi / Duplicate Yogi 最适合作为：

> **财富与灵性激活的高阶补充层。**

它能让财富分析更精细、更贴近个人活动路径，但不能代替传统财富承诺、分盘验证、大运和现实风控。
