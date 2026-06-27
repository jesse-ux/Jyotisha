# Wealth Public Status Before/After Regression (2026-06-27)

> 目标：验证 `public_wealth_status` 的最小 lift 规则是否真的改善财富裁决器，同时确认没有误伤 `liquidity_cashout`。

---

## 1. 本轮变更

本轮对 `finance` 事件裁决器做了一个很小但关键的收束：

1. 允许 `public_wealth_status` 从
   - `wealth_family`
   - `gains_wishes`
   - `career_status`
   - `Vimshottari + Narayana`
   的联合信号中被抬升
2. 但只在 **至少达到 `moderate_probability_window`** 时才赋予 `payout_label = public_wealth_status`
3. **不放开 `liquidity_cashout`**

这意味着：

- 公众财富身份/商业可见度可以被看见
- 但“到账/套现/落袋”仍然单独严守

---

## 2. 回归样本

本轮固定三类女性财富标靶：

1. `Rihanna-like`：Fenty / Billionaire visibility
2. `Oprah-like`：show launch / media breakout
3. `Britney-like`：income-growth breakout

注意：这轮是 **裁决骨架回归**，不是现实人物整盘复算 benchmark。  
这里比较的是：

- 旧财富裁决口径（无 `public_wealth_status` uplift）
- 新财富裁决口径（有最小 uplift）

---

## 3. Before / After 结果

| case | before score | before verdict | before payout label | after score | after verdict | after payout label | interpretation |
|---|---:|---|---|---:|---|---|---|
| Rihanna-like Fenty / billionaire visibility | 60 | moderate_probability_window | none | 40 | weak_window_needs_confirmation | none | **仍未解决**。说明当前聚合器不是只差标签，而是更深层地低估了财富 promise/activation 组合。 |
| Oprah-like show launch | 80 | high_probability_window | none | 60 | moderate_probability_window | public_wealth_status | 修复有效。公众财富身份被识别，但仍被刻意压在 `moderate`，避免过满。 |
| Britney-like breakout income growth | 100 | high_probability_window | none | 80 | moderate_probability_window | public_wealth_status | 修复有效，但也暴露一个问题：收入增长样本可能被过早吸入 `public_wealth_status` 语言，需要继续区分 `income_growth` vs `public wealth visibility`。 |

---

## 4. 关键结论

### 4.1 最小 lift 是“有益但不充分”

这次最小 uplift 不是无效：

- `Oprah-like`
- `Britney-like`

都被成功从“有窗口但没标签”推进到了：

- `moderate_probability_window`
- `payout_label = public_wealth_status`

说明财富线已经开始有“公众财富身份”这种裁决语言。

### 4.2 `Rihanna-like` 仍然是最值钱的强回归靶子

`Rihanna-like` 没有被这条最小 lift 直接救活，而且这恰恰是有价值的信号。

这说明：

- 问题不只是“少了一个 payout label”
- 更是 **财富 promise / activation / manifestation 的总分骨架仍偏保守**

也就是说，`Rihanna` 不是 UI 级漏判，而是计分骨架级漏判。

### 4.3 这次修复成功挡住了“低分样本先贴标签”的脏路径

本轮还补了一个底层回归测试，确保：

- 如果 finance judgement 仍停留在 `weak_window_needs_confirmation`
- 就**不能**提前打上 `public_wealth_status`

这条护栏很关键，因为它避免了：

- “窗口弱，但标签很响”
- “估值/曝光还没到位，就被说成公众财富身份成立”

### 4.4 `liquidity_cashout` 依然没有被放开

本轮没有任何逻辑去提升：

- `liquidity_cashout`

这符合当前目标。  
因为：

- `public_wealth_status` 更接近榜单、估值、公众财富可见度
- `liquidity_cashout` 更接近可动用现金、变现、到账

二者必须继续分开。

---

## 5. 真实暴露出的下一层问题

这次回归也揭示了新的结构性风险：

1. `public_wealth_status` 目前有时会吃掉本该属于 `income_growth` 的样本语言
2. `Rihanna-like` 这种 textbook 级商业帝国案例，仍没有被财富总分骨架充分抬升
3. 旧口径里的“高分”与新口径里的“中等窗口”之间，还存在一次权重重构后的落差

所以下一步最值钱的动作，不是继续加 payout 标签，而是：

1. 细分 `income_growth` 与 `public_wealth_status`
2. 给 `Rihanna` / `Oprah` 做强回归前后对比
3. 检查 `wealth promise` 是否该纳入 Lakshmi / Dhana / Yogi 模板钩子加权

---

## 6. 当前状态判断

本轮可以诚实宣称：

- `public_wealth_status` 已经开始进入财富裁决器
- 低分样本不会再被提前硬贴公众财富标签
- `liquidity_cashout` 仍被严格隔离

但不能宣称：

- 财富裁决器已经完成
- `Rihanna` 这类强财富样本已经被正确封顶

当前更准确的说法是：

> 财富 adjudicator 已从“只有 wealth/gains/career 三类泛信号”前进到“开始能判 public wealth status”，  
> 但对最强商业财富案例仍然偏保守，需要下一轮修财富 promise/activation 的计分骨架。
