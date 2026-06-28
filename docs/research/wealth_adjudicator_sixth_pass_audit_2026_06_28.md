# Wealth Adjudicator Sixth-Pass Audit (2026-06-28)

> 目标：把财富裁决输出从“单标签”推进到 `dominant_label + secondary_context` 的最小兼容骨架。

---

## 1. 本轮完成了什么

此前财富 adjudicator 的输出结构核心是：

- `score`
- `verdict`
- `payout_label`

这已经足够支撑基本回归，但有一个明显局限：

> 一次财富事件往往不只是一种标签，  
> 它常常还有“主导标签之外的辅助上下文”。

本轮没有贸然重做整套输出，而是采用最小兼容升级：

### 新增字段

- `dominant_label`
- `secondary_context`

### 保持兼容字段

- `payout_label`
- `verdict`

也就是说，旧调用方不会立刻坏掉，  
但新链路已经开始拥有更细颗粒的裁决表达层。

---

## 2. 当前输出行为

### 2.1 弱窗口

输出：

- `payout_label = None`
- `dominant_label = None`
- `secondary_context = []`

含义：

- 现在不仅知道“不该贴标签”
- 还明确知道“没有主导标签，也没有辅助上下文”

### 2.2 公众财富身份窗口

输出：

- `payout_label = public_wealth_status`
- `dominant_label = public_wealth_status`
- `secondary_context = ["career_status", "gains_wishes"]`

含义：

- 主导事件类型是公众财富身份
- 但它同时被事业可见度和收益网络支撑

### 2.3 收益爆发窗口

输出：

- `payout_label = income_growth`
- `dominant_label = income_growth`
- `secondary_context = ["wealth_family"]`

含义：

- 主导事件类型是收益增长
- 辅助上下文仍然带着财富承诺/财富家族层

---

## 3. 为什么这一步值钱

这一步的价值不在于“多了两个字段”，而在于：

### 3.1 开始把财富裁决从“单答案”推进到“分层答案”

以前：

- 系统只能说：这更像 `income_growth`

现在：

- 系统可以说：主导是 `income_growth`
- 但背后还有 `wealth_family` 的辅助上下文

这就是从“单标签命中”走向“有语义层次的裁决”。

### 3.2 为后面的 `dominant label + secondary context` 正式版打地基

本轮只是最小骨架：

- 没有上复杂 schema
- 没有强推多标签评分器
- 没有改老 verdict/payout 的兼容层

但它已经把最重要的迁移路径打通了：

> 旧结构还能活，  
> 新结构已经开始长。

---

## 4. 当前仍然保守的地方

本轮虽然新增了表达层字段，但仍然保持克制：

1. `dominant_label` 目前基本与 `payout_label` 同步
2. `secondary_context` 还只是轻量字符串列表
3. 没有引入复杂的 secondary 权重排序
4. 没有让多标签表达反向改写 `verdict`

这说明当前推进仍然遵守一个很好的节奏：

- 先让接口骨架存在
- 再让语义层次出现
- 最后才考虑让它影响更多推理层

---

## 5. 本轮和前五轮的关系

### 前五轮解决了

- 护栏
- 标签分流
- Promise 自动折叠
- 来源自动折叠
- 来源分散度轻量入分

### 第六轮解决了

- 输出表达层终于不再只有单标签

所以当前财富 adjudicator 已经开始同时拥有：

1. `promise folding`
2. `source folding`
3. `source weighting`
4. `label layering`

这说明它已经不再只是“规则列表 + 条件分支”，  
而是真的在长成一个有结构的 adjudication engine。

---

## 6. 下一轮最值钱的动作

按现在的 ROI，下一轮最值钱的依然是：

1. 接一个**轻量、真实、可回归**的 `Yogi` promise hook
2. 让 `dominant_label + secondary_context` 开始吃到 `Yogi` 这类辅助语义
3. 再决定是否要引入更强的 secondary context 排序或分层

---

## 7. 本轮状态判断

本轮可以诚实宣称：

- 财富 adjudicator 输出层已经从单标签推进到分层标签骨架
- 新字段 `dominant_label + secondary_context` 已进入主链
- 旧字段 `payout_label + verdict` 仍然兼容，没有破坏既有链路

但还不能宣称：

- 多标签财富裁决已经完全成熟
- `dominant_label` 与 `payout_label` 已彻底解耦
- secondary context 已具备复杂排序语义

更准确的说法是：

> 财富 adjudicator 已进入第六阶段：  
> 不仅会折叠 promise 和来源，还开始以分层输出的方式表达裁决结果。  
> 这让系统第一次具备了“主导标签 + 辅助上下文”的基本形状。
