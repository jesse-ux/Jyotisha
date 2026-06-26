# Bhrigu Pada 全事件专题冻结执行手册

> 来源：`4印度占星.docx`、`references/bhrigu-pada-dasha-marriage-counting.md`、`scripts/bhrigu_pada_dasha.py`、`scripts/jaimini.py`、`scripts/special_lagnas.py`
>
> **来源标签**: 【传统·现代大师 + Skill执行冻结】 — Bhrigu Pada / Arudha Pada 全事件推进标准动作
>
> **版本**：v1.0 | **最后更新**：2026-06-26

---

## 0. 来源等级与使用原则

本手册采用“分层信任”，不能把网上文章中的所有断语直接视为权威规则。

### A级：传统基础，可作为硬前提

- `Arudha Pada` 的基本概念与计算，属于 Parashara / Jaimini 传统中较稳固的内容。
- `Arudha` 表示现实世界中的投射、名声、显化、外界看到的结果。
- A1/A2/A7/A10/UL 等作为不同生活领域的显化点，可作为 Jaimini/Parashara 体系中的稳定底层。

### B级：现代大师/流派传承，可作为强参考

- Sanjay Rath 等现代传统占星师关于 Arudha Pada、Upapada、Dara Pada、Dasha 触发的讲解。
- Saptarishis Astrology 等公开文章中对 `Bhrigu Pada Dasha` 的整理。
- 这些内容可用于建立工作流，但必须保留流派口径说明。

### C级：网上文章/课程笔记/案例转述，只能作为线索

- 用户提供的 `4印度占星.docx`
- YouTube 讲座整理
- 网络课程笔记
- 未给出完整计算公式、未附可复核数据的案例文章

这些内容可以帮助发现技法，但不能单独变成硬断语。

### 使用原则

1. `Arudha Pada` 的底层计算可稳定使用。
2. `Bhrigu Pada Dasha` 的具体推进公式与事件断语，必须标注“流派/近似/待外部 oracle”。
3. 网上文章里的“事业、婚姻、财富事件示例”只能进入模板层，不能直接等同传统定论。
4. 凡涉及具体年份、月份、婚姻次数、健康危机，必须与 Dasha / Transit / 分盘 / 现实事件交叉。

---

## 1. 用途

本手册把 `Bhrigu Pada Dasha` 从“婚姻计时专题”扩展为**全事件推进法的执行框架**。

适用场景：

1. 用户问事业突破、名声、职业断层
2. 用户问婚姻、长期关系、伴侣事件
3. 用户问财富进账、收益、资产变化
4. 用户问子女、创作、教育成果
5. 用户问危机、疾病、事故、隐秘转折

核心纠偏：

> Bhrigu Pada Dasha 不是只能看婚姻。它的核心是用不同 Arudha Pada 的主星作为对应事件的控制行星。

更严谨地说：

> `Arudha Pada` 的领域对应相对稳固；`Bhrigu Pada Dasha` 的推进触发规则属于流派化实践，当前 skill 只能把它作为辅助推进确认层，而不是单独主判体系。

---

## 2. 当前冻结边界

### 已冻结

1. `references/bhrigu-pada-dasha-marriage-counting.md` 已整理婚姻计时与婚姻计数法
2. `scripts/bhrigu_pada_dasha.py` 已有通用近似推进、婚姻窗口、BCP 整合
3. `scripts/jaimini.py` 已有 A1-A12 / UL 的 Arudha Pada 计算
4. `scripts/special_lagnas.py` 已有 A10 / Karma Pada
5. `full-reading.modules.bhrigu_pada_dasha` 已能输出 Bhrigu Pada Dasha 模块

### 尚未完全冻结

1. Bhrigu Pada 的多事件 API / CLI 入口
2. 基于 `A2 / A5 / A7 / A8 / A10 / A11 / UL` 的统一事件模板
3. 事业、财富、健康、子女等非婚姻案例 oracle
4. 不同 Bhrigu 子流派推进速率的外部黑盒对照

结论：

> 当前可把 Bhrigu Pada 用作全事件“辅助推进/确认层”，但不能把其近似计算包装成传统软件级精密闭环。

---

## 3. 核心原理

Bhrigu Pada 的事件判断顺序：

1. 先确定事件领域
2. 找到对应 Arudha Pada
3. 找到该 Pada 的主星
4. 将 Pada 主星视作该事件的控制行星
5. 观察控制行星在推进盘/年龄点中是否进入关键宫位、三方四正、合相或互相连接
6. 用 Dasha、Transit、D9/D10/D60 等系统交叉验证

一句话：

> 事件不是看“随便哪颗推进行星”，而是看该事件对应 Arudha Pada 的主星如何被推进与触发。

---

## 4. 事件领域与 Pada 对照

| 事件 | 主要 Pada | 控制行星 | 辅助证据 |
|---|---|---|---|
| 自我形象 / 公众观感 | A1 / AL | AL 主星 | Lagna lord、Moon、Sun |
| 财富积累 / 现金流 | A2 | A2 主星 | 2宫主、11宫主、Jupiter、Venus |
| 勇气 / 写作 / 手足 | A3 | A3 主星 | 3宫主、Mars、Mercury |
| 房产 / 家庭 / 母亲 | A4 | A4 主星 | 4宫主、Moon、Mars |
| 子女 / 创作 / 教育成果 | A5 | A5 主星 | 5宫主、Jupiter、D7 |
| 病痛 / 敌人 / 官非 | A6 | A6 主星 | 6宫主、Mars、Saturn、D6/D30 |
| 婚姻 / 伴侣 / 合伙 | A7 | A7 主星 | 7宫主、Venus/Jupiter、DK、D9 |
| 危机 / 手术 / 突变 | A8 | A8 主星 | 8宫主、Saturn、Mars、D30 |
| 福德 / 远行 / 宗教 | A9 | A9 主星 | 9宫主、Jupiter、D20 |
| 事业 / 名声 / 职业事件 | A10 | A10 主星 | 10宫主、AmK、Sun、D10 |
| 收益 / 社群 / 愿望实现 | A11 | A11 主星 | 11宫主、Jupiter、D11 |
| 婚姻承诺 / 床第 / 损耗 / 远方 | UL / A12 | UL 主星 | 12宫主、Venus、D9 |

---

## 5. 强制执行顺序

### Step 1. 先确认 D1 承诺

Bhrigu Pada 不负责凭空制造事件。
若 D1 没有承诺，只能当作弱提示。

### Step 2. 确定事件 Pada

例：

- 事业：A10
- 财富：A2 / A11
- 婚姻：A7 / UL
- 子女：A5
- 健康危机：A6 / A8

### Step 3. 找 Pada 主星

Pada 所在星座的主星，就是本事件的控制行星。

注意：

- 本系统通常使用七曜主星
- Rahu/Ketu 共主规则必须声明流派边界
- 当前仓内共主仲裁仍有尾差时，不要假装无争议

### Step 4. 看控制行星推进

重点观察：

1. 控制行星进入事件相关宫位
2. 控制行星与本命控制行星合相
3. 控制行星与事件 Karaka 形成三方/四正/合相
4. 控制行星进入 Pada 所在星座或其三方
5. 推进行星与 D1 / D9 / D10 中同主题点互相连接

### Step 5. 用领域分盘验证

不能只看 D1。

- 婚姻：D9
- 事业：D10
- 子女：D7
- 财富：D2 / D11
- 健康危机：D6 / D8 / D30
- 灵性/福德：D20 / D9

### Step 6. 用 Dasha / Transit 收敛

Bhrigu Pada 只作为推进确认层时，必须至少再有一层：

- Vimshottari
- Chara Dasha
- Transit / Double Transit
- BCP
- Varshaphala

---

## 6. 事业事件模板

主要点：

- A10
- A10 主星
- 10宫主
- Amatyakaraka (AmK)
- Sun
- D10

重断条件：

1. D1 有事业承诺
2. A10 主星被推进触发
3. D10 同步出现强化或压力
4. Dasha / Transit 同步激活 10宫、A10、AmK 或 Sun

允许输出：

- 升迁
- 出名
- 职业转折
- 公众身份变化
- 项目发布

禁止输出：

- 只因 A10 主星推进就断必升职

---

## 7. 财富事件模板

主要点：

- A2
- A11
- 2宫主
- 11宫主
- Jupiter
- Venus
- D2 / D11

重断条件：

1. A2/A11 主星被推进触发
2. 2宫/11宫链有承诺
3. D2 或 D11 不相反
4. Dasha 同步触发财富星、财富宫或 Yogi 点

允许输出：

- 收入增长
- 大额进账
- 合作收益
- 资源曝光

禁止输出：

- 忽略财务承诺，单凭 A2 推进断暴富

---

## 8. 婚姻事件模板

主要点：

- A7
- UL / A12
- 7宫主
- Venus / Jupiter
- DK
- D9

重断条件：

1. A7 或 UL 主星被推进触发
2. D9 支持
3. Dasha/Transit 同步激活 7宫链
4. 现实年龄与关系环境允许

允许输出：

- 进入重要关系
- 订婚/结婚窗口
- 伴侣事件
- 合伙关系形成

禁止输出：

- 把“持续一年以上认真关系”的计数直接等同法律婚姻次数

---

## 9. 子女 / 创作事件模板

主要点：

- A5
- 5宫主
- Jupiter
- D7
- Moon

重断条件：

1. A5 主星被推进触发
2. 5宫链与 Jupiter 有支持
3. D7 支持
4. Dasha/Transit 同步激活

允许输出：

- 生育窗口
- 子女事件
- 作品发布
- 教育成果

---

## 10. 健康 / 危机事件模板

主要点：

- A6
- A8
- 6宫主
- 8宫主
- Saturn / Mars
- D6 / D8 / D30

重断条件：

1. A6/A8 主星被推进触发
2. D6/D8/D30 同步见压
3. Dasha/Transit 同步激活
4. 医疗现实或既往事件支持

允许输出：

- 健康压力
- 手术/治疗窗口
- 危机处理
- 官非/敌人事件

禁止输出：

- 单凭 Bhrigu Pada 断死亡或重病

---

## 11. 与 BCP 的关系

BCP 与 Bhrigu Pada 不同：

- `BCP`：宏观自然周期，适合看年龄阶段主题
- `Bhrigu Pada`：事件控制行星推进，适合看具体领域触发

推荐顺序：

1. 先用 BCP 看年龄主题
2. 再用 Bhrigu Pada 找事件控制行星
3. 最后用 Dasha / Transit 收敛

---

## 12. 置信度分级

### 低置信

- 只有 Bhrigu Pada 信号
- D1/D9/D10/Dasha 不支持

输出为：

- “提示”
- “可观察窗口”

### 中置信

- Bhrigu Pada + D1 承诺
- 或 Bhrigu Pada + Dasha 激活

输出为：

- “较值得关注的窗口”

### 高置信

必须同时满足：

1. D1 承诺
2. 对应分盘支持
3. Bhrigu Pada 控制行星推进触发
4. Dasha/Transit 至少一项同步

输出为：

- “高优先级事件窗口”

---

## 13. 当前不能伪装成闭环的部分

以下内容必须保留边界：

1. 不同 Bhrigu 子流派的精确推进速率
2. JHora / Shri Jyoti Star / 网页工具的口径差异
3. 多事件 API 尚未统一产品化
4. 非婚姻领域案例 oracle 不足
5. Rahu/Ketu 共主是否参与 Pada 主星，需要按流派声明

---

## 14. 工业化字段骨架

后续模板化建议字段：

- `event_type`
- `target_pada`
- `pada_sign`
- `pada_lord`
- `progressed_lord_position`
- `natal_lord_connection`
- `event_karaka_connection`
- `target_varga_support`
- `dasha_support`
- `transit_support`
- `confidence`
- `narrative_short`
- `narrative_deep`
- `boundary_note`

---

## 15. 最短执行卡

如果时间很紧，至少执行：

1. 确定用户事件类型
2. 找对应 Pada
3. 找 Pada 主星
4. 看控制行星推进是否触发事件宫/本命点/Karaka
5. 看领域分盘
6. 看 Dasha/Transit
7. 给出置信度与边界

只做到前 4 步，叫**推进提示**。
做到第 7 步，才叫**事件窗口判断**。

---

## 16. 结论

Bhrigu Pada 现在应从“婚姻技巧”升级为：

> **基于 Arudha Pada 主星的全事件推进确认模块。**

它的价值在于为事业、财富、婚姻、子女、危机等主题提供额外时间确认层。
它不能替代 Vimshottari、Chara、Transit、分盘和现实事件校验。
