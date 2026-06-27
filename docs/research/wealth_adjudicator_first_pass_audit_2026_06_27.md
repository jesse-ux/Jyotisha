# Wealth Adjudicator First-Pass Audit (2026-06-27)

> 目标：给财富事件裁决器建立第一批可回归标靶，避免“发财”成为模糊大词。  
> 本轮先冻结女性样本，重点观察 `income_growth / public_wealth_status` 两类事件。

---

## 1. 审计方法

本轮按 `event_judgment_wealth.md` 的四层框架看财富事件：

1. `wealth promise`
2. `wealth activation`
3. `wealth manifestation`
4. `payout label`

并同时观察以下结构信号：

- `wealth_family`
- `gains_wishes`
- `career_status`
- `Vimshottari + Narayana`
- `Shadbala strong planets`
- `template hooks`（Lakshmi / Yogi）

---

## 2. 第一批标靶集

| case | real-world event type | payout label | promise verdict | activation verdict | manifestation verdict | payout-label verdict | final adjudicator verdict | miss type | suspected missing features |
|---|---|---|---|---|---|---|---|---|---|
| Oprah Winfrey - The Oprah Winfrey Show launch (1986-09-08) | media breakout / wealth path opening | public_wealth_status | medium | weak (`wealth_family L1`) | medium | weak | under-lifted | activation weak | public wealth status should combine career + gains + wealth instead of waiting for pure wealth-family hit |
| Britney Spears - ...Baby One More Time release (1998-10-23) | breakout income growth | income_growth | medium | strong (`gains_wishes L3`) | medium | medium | moderate window | manifestation split | income growth vs public status vs career visibility need cleaner separation |
| Priyanka Chopra - Quantico breakout (2015-09-27) | global visibility / commercial expansion | public_wealth_status | medium | weak (`career_status L1`) | medium | weak | under-lifted | payout-label weak | public wealth status not lifted from career-only signal |
| Princess Diana - Royal wedding visibility event (1981-07-29) | status elevation with wealth visibility implications | public_wealth_status | medium | strong (`career_status L4`) | medium | medium | moderate but not wealth-specific | manifestation split | separate status visibility from actual wealth accumulation |
| Rihanna - Fenty Beauty launch (2017-09-08) | beauty empire launch / business wealth visibility | public_wealth_status | strong | weak (`wealth_family L1`) | strong | weak | **under-lifted** | **payout-label failure** | public wealth status not lifted from Venus-led 2H promise + business empire context |
| Rihanna - Forbes billionaire recognition (2021-08-04) | public billionaire status | public_wealth_status | strong | weak (`wealth_family L1`) | strong | weak | **under-lifted** | **payout-label failure** | billionaire/public status not distinguished from simple 2H activation |

---

## 3. 关键发现

### 3.1 财富线目前对 `public_wealth_status` 的识别不够敏锐

当前系统更容易识别：

- `career_status`
- `gains_wishes`

但对以下更复杂标签仍然偏弱：

- `public_wealth_status`
- `liquidity_cashout`

这说明财富聚合器还更像“事业/收益聚合器”，还不是完整的财富事件标签器。

### 3.2 `income_growth` 比 `public_wealth_status` 更容易被点亮

在女性样本里：

- `Britney Spears` 的音乐爆发，对 `gains_wishes` 是明显强信号（`L3`）
- 但 `Oprah / Priyanka / Diana` 这类偏“身份与商业可见度跃迁”的事件，并没有被同样稳定地抬升

这说明目前的财富线更偏向：

- 收益/流量/事业势能

而不是：

- 公众财富身份
- 商业帝国型财富地位

### 3.3 财富线已经出现婚恋线的同构缺陷

财富线也出现了和婚恋线类似的第四类缺陷：

## `payout-label failure`

定义：

- 旧体系或现实世界事件明确成立
- 新聚合器有部分支持信号
- 但没有把事件抬成正确的财富标签

当前疑似样本：

- `Oprah Winfrey`
- `Priyanka Chopra`
- `Rihanna`

### 3.4 `Rihanna` 是财富线当前最值钱的校准靶子

`Rihanna` 的两个事件非常适合作为财富 adjudicator 的强回归样本：

1. `Fenty Beauty launch`
2. `Forbes billionaire recognition`

原因：

- 本命财富 promise 很强（仓内既有 case study 已确认）
- 现实世界财富与商业地位极明确
- 当前聚合器仍只给出 `wealth_family L1`

这类样本几乎是 textbook 级别的 `payout-label failure`。

---

## 4. 初步缺陷类型学

1. `promise weak`
2. `activation/convergence weak`
3. `manifestation split`
4. `payout-label failure`

目前这批女性样本里，最主要的是：

- `activation/convergence weak`
- `manifestation split`
- `payout-label failure`

---

## 5. 下一轮修复重点

1. 让 `public_wealth_status` 不只依赖 `wealth_family`，而要允许 `career_status + gains_wishes + wealth promise` 联合抬升
2. 区分：
   - `income growth`
   - `asset accumulation`
   - `liquidity/cash-out`
   - `public wealth visibility`
3. 增加女性财富样本：
   - `Rihanna`
   - `Oprah`
   - `Britney`
   - `Taylor Swift` / `Beyonce`（若仓内已有稳定数据）
4. 将 `Lakshmi / Yogi / Dhana` 模板钩子纳入财富 lift 候选，而不是只留在解释层

---

## 6. 第一版调权建议（草案）

### 6.1 对 `public_wealth_status` 的 lift 条件

当同时满足以下两类信号时，不应继续停留在 `L1 wealth_family`：

1. **强财富 promise**
   - 2H / 11H / Jupiter / Venus / Mercury 明显支持
   - 或模板命中：`lakshmi_dhana_activation_chain` / `yogi_asc_tight_orb_wealth`
2. **事业/收益/公众可见度触发**
   - `career_status`
   - `gains_wishes`
   - 职业商业化事件标签（品牌、发行、上市、公众财富排名）

### 6.2 拟新增规则

对于 `public_wealth_status`：

- 若 `wealth_family >= L1`
- 且 `career_status` 或 `gains_wishes` 至少一项存在
- 且财富 promise 为 `medium/strong`

则允许把最终 verdict 从 `weak/under-lifted` 抬升到 `moderate_probability_window` 候选，而不是直接卡死在 `L1`。

---

## 7. 版本备注

- 这是第一轮财富审计，不是最终 benchmark
- 本轮目标是先把财富事件标签拆开，而不是直接宣称“财富 timing 已经精准”
