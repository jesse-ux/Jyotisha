# Wealth Adjudicator Third-Pass Audit (2026-06-27)

> 目标：把 `wealth_promise_strength` 从“手工喂入的测试字段”推进到“可由仓内真源自动折叠”的真实裁决输入。

---

## 1. 本轮完成了什么

本轮没有新增财富标签，也没有继续扩 promise 来源。  
只完成了一件关键工作：

**让 `strict_workflow -> _collect_strict_evidence("finance")` 能从**

- `full-reading.modules.yogas_doshas.dhana_yogas`

**自动折叠出**

- `wealth_promise_strength`

当前折叠规则非常克制：

- 至少一条 `strong` Dhana Yoga -> `level = strong`
- 否则至少一条 `moderate` Dhana Yoga -> `level = moderate`
- 否则 -> `weak`
- 没有 `dhana_yogas` -> `None`

并产出结构：

```json
{
  "level": "strong",
  "source": "dhana_yogas",
  "count": 2
}
```

---

## 2. 为什么这一步值钱

前两轮虽然已经把财富裁决器推进到：

- `public_wealth_status` 行为护栏
- `income_growth` vs `public_wealth_status` 分流
- `wealth_promise_strength` 显式入分

但那时还有一个明显的工程短板：

> `wealth_promise_strength` 还是手工喂进去的，不是真正来自 skill 自己的知识资产。

本轮之后，这个短板第一次被抹平了一部分。  
也就是说，财富裁决器已经开始从仓内现成的财富真源里，自己长出 promise 分。

---

## 3. 回归结果

### 3.1 自动 promise 折叠验证

使用含有：

- `D2`
- `D10`
- `Shadbala`
- `Ashtakavarga`
- `Vimshottari + Narayana`
- `wealth/gains/career convergence`
- `dhana_yogas = [strong, moderate]`

的 finance strict evidence 场景，当前返回：

- `present_evidence.wealth_promise_strength = {"level":"strong","source":"dhana_yogas","count":2}`
- `event_judgement.score = 100`
- `event_judgement.verdict = moderate_probability_window`
- `event_judgement.payout_label = public_wealth_status`

### 3.2 这里最重要的不是满分，而是“满分仍被压在 moderate”

这个现象其实是好的，而不是坏的。

它说明当前财富裁决器的边界依旧保持保守：

- 即便完整证据场景把分数顶满
- 也不会因为 finance score 很高就直接升级到过满承诺

这和项目当前的真实边界是一致的：

> 我们在提升财富裁决器的结构成熟度，  
> 但还没有宣布“精确财富应期已全球封顶”。

---

## 4. 当前状态相较前两轮的提升

### 第一轮

- 加护栏
- 堵住弱窗口乱贴 `public_wealth_status`

### 第二轮

- `wealth_promise_strength` 显式入分
- `income_growth` 与 `public_wealth_status` 开始分家

### 第三轮（本轮）

- `wealth_promise_strength` 不再只是手工输入
- 它开始从仓里的 `dhana_yogas` 自动生成

所以本轮的本质是：

> 财富 adjudicator 从“能接收 promise 分”进一步走到了“能自己从真源提 promise 分”。

---

## 5. 仍未完成的部分

这轮虽然很值钱，但还没有到终局：

1. `wealth_promise_strength` 目前只吸收了 `dhana_yogas`
2. `lakshmi_dhana_activation_chain` 还没有自动接入
3. `yogi_asc_tight_orb_wealth` 还没有自动接入
4. `asset_accumulation` vs `public_wealth_status` 还没有专门回归样本
5. `dominant label + secondary context` 还没建立

---

## 6. 下一轮最值钱的动作

如果继续按 ROI 排序，下一轮最值钱的是：

1. 把 `lakshmi_dhana_activation_chain` 接成第二个自动 promise hook
2. 把 `yogi_asc_tight_orb_wealth` 接成第三个自动 promise hook
3. 然后再看是否需要从单标签走向：
   - `dominant label`
   - `secondary context`

这样我们就能处理你前面提到的下一类样本：

- 收益爆发很强
- 同时公众事业可见度也不低

而不是只能二选一硬切。

---

## 7. 本轮状态判断

本轮可以诚实宣称：

- 财富 adjudicator 已经开始自动吸收仓内 `Dhana Yoga` 真源
- `wealth_promise_strength` 已从手工测试输入升级为自动折叠输入
- 当前保守边界仍在，没有因为自动 promise 折叠就开始乱给高承诺

但还不能宣称：

- 全部财富 promise 资产已自动闭环
- `Lakshmi / Yogi / Dhana` 三路来源都已折叠完成

更准确的说法是：

> 财富 adjudicator 已进入“自动 promise 折叠”的第三阶段，  
> 现在不再只是规则聚合器，而开始真正从 skill 自己的财富知识资产中抽取裁决分数。
