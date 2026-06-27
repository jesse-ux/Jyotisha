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

---

## 6. 版本备注

- 这是第一轮财富审计，不是最终 benchmark
- 本轮目标是先把财富事件标签拆开，而不是直接宣称“财富 timing 已经精准”
