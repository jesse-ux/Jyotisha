# RTN + 高阶 D9 专题冻结执行手册

> 来源：`3印度占星.docx`、`references/rashi-tulya-navamsa-root-impulse.md`、`references/high-order-d9-execution-guide.md`、`scripts/rashi_tulya_navamsa.py`
>
> **来源标签**: 【传统·现代大师 + Skill执行冻结】 — Rashi Tulya Navamsa / 高阶 D9 返照标准动作
>
> **版本**：v1.0 | **最后更新**：2026-06-26

---

## 1. 用途

本手册把 `Rashi Tulya Navamsa (RTN)` 与高阶 D9 异象，从“概念已存在”冻结成可稳定执行的专题工作流。

适用场景：

1. 婚姻/关系已经有 D1 与 D9 线索，但解释仍不够深入
2. 需要判断某颗星在 D9 中的深层动机如何投射回 D1
3. 需要说明“表面承诺”和“灵魂兑现”为什么不同步
4. 需要处理 Yama / Preta / Pisacha / Rakshasa 这类高阶 D9 凶性提示
5. 需要将文章级 D9 细节模板工业化

---

## 2. 当前冻结边界

### 已冻结

1. `RTN` 已在主 skill 中登记
2. `scripts/rashi_tulya_navamsa.py` 已存在映射引擎
3. 已有 `RTN_HOUSE_NAMES`
4. 已有 `GUNAS`
5. 已有凶星组合命名：
   - `Mars + Saturn` → `Yama Yoga`
   - `Saturn + Rahu/Ketu` → `Preta Yoga`
   - `Mars + Rahu` → `Rakshasa Yoga`
   - `Mars + Ketu` → `Pisacha Yoga`
6. `high-order-d9-execution-guide.md` 已明确 Pushkara / Vargottama / RTN 的角色边界

### 尚未完全冻结

1. `Yama / Preta / Pisacha` 的分段式 amsa 区间识别
2. D9 第七主映射回 D1 后的统一婚姻危机模板
3. D9 返照 D1 的事件兑现规则
4. 高阶 D9 异象的名人案例 oracle

结论：

> 当前 RTN 可以作为高阶解释层和关系深层动机层使用，但不能单独作为事件发生或婚灾必然性的主证据。

---

## 3. 技法定位

`RTN` 的核心问题不是“会不会发生事件”，而是：

1. 某颗星在更深层的 D9 中被什么动机驱动
2. D9 的灵魂层状态如何投射回 D1 的现实宫位
3. 关系、欲望、恐惧、责任、智慧等主题为什么会以某种方式表现
4. 哪些 D9 内在压力会在 D1 的现实场景中显形

一句话：

> RTN 是 D9 对 D1 的“深层动机返照”，不是独立 timing 引擎。

---

## 4. 强制执行顺序

### Step 1. 先完成普通 D1 / D9 判断

必须先看：

- D1 承诺
- D9 上升
- D9 第七宫
- D9 第七主
- D9 Venus / Jupiter
- DK 在 D9 的状态

没有这一步，不允许直接跳到 RTN 重断。

### Step 2. 再看 Vargottama 与 Pushkara

顺序：

1. `Vargottama` 判断一致性
2. `Pushkara` 判断吉化/保护
3. 再进入 `RTN`

原因：

> Vargottama / Pushkara 是加权层；RTN 是动机解释层。顺序反了，容易把解释当承诺。

### Step 3. 执行 RTN 映射

读取：

- `scripts/rashi_tulya_navamsa.py`

最少输出：

- D9 行星
- D9 星座
- D9 宫位
- 映射回 D1 后的宫位
- RTN 宫位名
- D1 合相
- Guna
- 凶性组合提示

### Step 4. 判断映射宫位性质

映射回 D1 后，优先看：

- `1 / 4 / 5 / 7 / 9 / 10 / 11`：较容易显化与承载
- `6 / 8 / 12`：更容易形成压力、隐患、债务、断裂或隐秘代价

婚姻专题中，尤其关注：

- Venus
- Jupiter
- DK
- D9 第七主
- D9 上升主

### Step 5. 检查凶性组合

当前已冻结为“警告模板”的组合：

- `Mars + Saturn`：Yama Yoga
- `Saturn + Rahu/Ketu`：Preta Yoga
- `Mars + Rahu`：Rakshasa Yoga
- `Mars + Ketu`：Pisacha Yoga

使用规则：

> 这些组合只能作为高阶风险提示，不得单独断死亡、灾厄、精神异常或婚姻必破。

---

## 5. RTN 宫位冻结口径

### 1宫 Lagnamsa

深层动机直接投射到人格、自我、外在表现。

### 2宫 Dhanamsa

投射到财富、家庭、价值观、语言。

### 3宫 Vikramsa

投射到勇气、表达、竞争、手足、主动选择。

### 4宫 Sukhamsa

投射到家庭、安全感、母亲、居住、内在满足。

### 5宫 Putramsa

投射到恋爱、创造力、子女、智性与前世功德。

### 6宫 Ariamsa

投射到债务、敌人、病痛、服务、争执。
婚姻专题中要警惕关系进入劳动、消耗、争端状态。

### 7宫 Kalatramsa

投射到伴侣、合伙、公开关系。
婚姻专题中这是高价值点，但仍要看 D9 与 Dasha。

### 8宫 Randhramsa

投射到危机、秘密、性、共同财务、突变。
婚姻专题中代表深层不稳定和隐秘代价。

### 9宫 Bhagyamsa

投射到信仰、远行、父亲、导师、福德。

### 10宫 Karmamsa

投射到事业、身份、公共成就和责任。

### 11宫 Labhamsa

投射到收益、人脉、愿望实现、团体资源。

### 12宫 Vyayamsa

投射到损耗、隐退、远方、床第、灵修、隔离。
婚姻专题中要警惕分居、远距、隐秘关系或牺牲感。

---

## 6. 高阶 D9 异象冻结口径

### Yama Yoga

触发：

- RTN 层或 D9 返照层中 `Mars + Saturn` 强接触

允许输出：

- 高压、事故、病痛、关系僵死、阻断感
- 需要 Dasha / Transit 才会真正激活

禁止输出：

- 单凭此组合断死亡

### Preta Yoga

触发：

- `Saturn + Rahu`
- `Saturn + Ketu`

允许输出：

- 祖先业力、慢性压力、旧债、关系中挥之不去的阴影

禁止输出：

- 单凭此组合断短寿或必有灵异问题

### Rakshasa Yoga

触发：

- `Mars + Rahu`

允许输出：

- 冲动、暴烈、攻击性、欲望失控、神经系统压力

禁止输出：

- 单凭此组合断犯罪或暴力事件

### Pisacha Yoga

触发：

- `Mars + Ketu`

允许输出：

- 切断、毒性关系、隐性攻击、突然抽离、天蝎式深层压力

禁止输出：

- 单凭此组合断鬼魅、附体或极端结论

---

## 7. 婚姻专题冻结模板

### 轻断

条件：

- 只完成 RTN 映射
- 未见 Dasha 激活
- D1/D9 没有多重同向证据

输出：

- “这说明关系深层动机倾向于……”
- “这个结构更像内在模式，不宜单独作为事件判断”

### 中断

条件：

- RTN 映射落入 `6 / 8 / 12`
- D9 第七主 / DK / Venus 至少一项受压

输出：

- “关系深层存在消耗、隐秘或抽离倾向”
- “需要结合 Dasha 确认是否进入事件层”

### 重断

条件必须同时满足：

1. D1 第七宫链受损
2. D9 第七主 / Venus / Jupiter / DK 受损
3. RTN 映射落入 `6 / 8 / 12` 或触发凶性组合
4. Dasha / Bhukti / Transit 正在激活相关星体

此时才可以讨论：

- 婚姻深层危机
- 隐秘关系
- 分居/抽离
- 关系业力沉重

---

## 8. 与其他系统的硬联动

### 与 Tithi Lord

- `Tithi Lord` 给出情感水龙头
- RTN 给出这颗水龙头的深层驱动
- 若 `Tithi Lord` 在 RTN 中落入 `6 / 8 / 12`，关系底色更易带有消耗或隐秘代价

### 与 Darakaraka

- DK 在 D9 是配偶深层象征
- DK 的 RTN 映射说明配偶/关系主题会落到现实生活的哪个宫位

### 与 Vargottama

- Vargottama 表示一致性
- 若 Vargottama 星在 RTN 中也映射到关键宫位，该星成为更强的解释锚点

### 与 Pushkara

- Pushkara 提供保护/吉化
- 若 RTN 显示压力，但 Pushkara 同时存在，可降低断语强度

### 与 Dasha

- 没有 Dasha 激活时，只做结构解释
- 有 Dasha 激活时，才进入事件风险判断

---

## 9. 输出模板口径

### 可说

- “RTN 显示这颗星的深层动机投射到第 X 宫”
- “这更像关系中的内在驱动力，而不是单独的事件承诺”
- “若 Dasha 同时激活，才会进入现实事件层”

### 不可说

- “只因 RTN 落 8 宫就一定婚灾”
- “只因 Yama/Preta/Pisacha 就一定出灾”
- “只因 D9 异象就推翻 D1/Dasha”

---

## 10. 工业化字段骨架

后续模板化建议字段：

- `planet`
- `d9_sign`
- `d9_house`
- `mapped_d1_house`
- `rtn_house_name`
- `d9_dignity`
- `d1_conjunctions`
- `guna`
- `curse_yoga`
- `relationship_relevance`
- `dasha_activation`
- `confidence`
- `narrative_short`
- `narrative_deep`
- `boundary_note`

---

## 11. 最短执行卡

如果时间很紧，至少执行：

1. 看 D1 第七宫链
2. 看 D9 第七宫链
3. 看 Venus / Jupiter / DK
4. 跑 RTN 映射
5. 标记映射宫位是否落 `6 / 8 / 12`
6. 检查 Yama / Preta / Rakshasa / Pisacha 类提示
7. 用 Dasha 判断是否能升级到事件层

只做到前 6 步，叫**深层结构判断**。
做到第 7 步，才允许进入**事件风险判断**。

---

## 12. 当前未冻结但必须记住的边界

以下内容目前不能伪装成完全闭环：

1. Yama / Preta / Pisacha 的传统分段 amsa 全量枚举
2. D9 第七主返照 D1 的硬算法
3. RTN 异象的名人案例 oracle
4. RTN 与具体事件日期的直接 timing 公式

处理方式：

- 可以作为高阶解释层
- 必须与 D1、D9、Dasha 至少两层交叉
- 重断必须保留置信度和边界说明

---

## 13. 结论

RTN + 高阶 D9 现在应该被视为：

> **D9 深层动机与现实投射的一级解释模块。**

它最适合解释“为什么这个 D9 结构会在现实中表现为某种关系模式、欲望模式或危机模式”，但不应单独承担事件承诺和精确应期。
