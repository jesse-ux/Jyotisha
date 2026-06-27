# Wealth Adjudicator Fourth-Pass Audit (2026-06-28)

> 目标：把 `wealth_promise_strength` 从“单一路径强弱标签”推进到“带来源结构的 promise folding engine”。

---

## 1. 本轮核心变化

前三轮我们已经完成：

1. `public_wealth_status` 行为护栏
2. `income_growth` 与 `public_wealth_status` 分流
3. `dhana_yogas -> wealth_promise_strength` 自动折叠

本轮继续往前走了一层：

**`wealth_promise_strength` 不再只返回**

- `level`
- `count`

而开始返回：

- `primary_source`
- `supporting_sources`
- `source_diversity`

当前输出结构变成：

```json
{
  "level": "strong",
  "primary_source": "dhana_lakshmi_hooks",
  "supporting_sources": ["dhana", "lakshmi"],
  "count": 2,
  "source_diversity": 2
}
```

---

## 2. 为什么这一步重要

用户此前指出了一个非常关键的工程问题：

> “更多 = 更强”还不够，  
> 还要区分“同一路径重复命中”与“多条独立财富路径共同命中”。

这轮正是在解决这个问题。

以前的 promise folding 更像：

- 有强格局 / 没有强格局

现在开始变成：

- 财富承诺有多强
- 它主要来自哪条路径
- 是单一来源，还是多来源交叉支持

这意味着我们第一次开始把“来源分散度”当成财富 promise 可信度的一部分。

---

## 3. 本轮回归边界

### 3.1 纯 Dhana 路径

输入：

- 两条 `Dhana Yoga`
- 无 `Lakshmi`

当前自动折叠输出：

```json
{
  "level": "strong",
  "primary_source": "dhana_yogas",
  "supporting_sources": ["dhana"],
  "count": 2,
  "source_diversity": 1
}
```

### 3.2 Dhana + Lakshmi 双路径

输入：

- 一条 `Dhana Yoga`
- 一条 `Lakshmi Yoga`

当前自动折叠输出：

```json
{
  "level": "strong",
  "primary_source": "dhana_lakshmi_hooks",
  "supporting_sources": ["dhana", "lakshmi"],
  "count": 2,
  "source_diversity": 2
}
```

这个差别就是本轮真正新增的硬度。

---

## 4. 关键结论

### 4.1 Promise folding 已从“有无强信号”进入“来源结构化”

现在财富 promise 已经不只是一个粗粒度强弱值。

它开始回答：

- 是 `Dhana` 一路在说话
- 还是 `Dhana + Lakshmi` 两路同时在说话

这对后面做二级权重非常关键。

### 4.2 `source_diversity` 比单纯 `count` 更值钱

`count = 3` 不一定比 `count = 2` 更强。

因为：

- 3 条都来自 `Dhana`
- 和 `Dhana + Lakshmi + Yogi` 三路各 1 条

在解释可靠性上不是一回事。

本轮把这个结构性差异正式落入了主链。

### 4.3 这仍然是保守推进，不是一次性做胖

本轮没有硬接完整 `Yogi` 系统。

原因很明确：

- 当前主链没有结构化的 Yogi 输出
- 若强行接入，容易制造“看似高级、其实假结构”的问题

所以本轮只把：

- `Dhana`
- `Lakshmi`

两路先接实，并给 `Yogi` 留出下一轮的合理接入口。

---

## 5. 目前还没完成的部分

1. `Yogi` 还没有进入自动 promise folding
2. `primary_source` 目前仍是规则化字符串，不是更细颗粒的 source ranking
3. `source_diversity` 还没有真正反馈到 finance judgement 权重
4. `dominant label + secondary context` 仍未启动

---

## 6. 下一轮最值钱的动作

在当前节奏下，下一轮最值得做的是：

1. 给 `Yogi` 接入一个**轻量但真实**的 promise hook
   - 不重建整套 Yogi 系统
   - 只接可结构化、可验证的正向财富支持信号
2. 让 `source_diversity` 真正进入二级权重
3. 再决定是否需要从单标签推进到：
   - `dominant label`
   - `secondary context`

---

## 7. 本轮状态判断

本轮可以诚实宣称：

- 财富 adjudicator 已经不只会自动提取 promise 强弱
- 它开始区分 promise 来源的分散度与结构
- `Dhana` 与 `Lakshmi` 不再被揉成一个黑箱来源

但还不能宣称：

- `Yogi` 已正式进入自动 folding
- `source_diversity` 已经回写到最终裁决权重

更准确的说法是：

> 财富 adjudicator 已进入“promise source folding”第四阶段，  
> 开始从“自动提取强弱”升级到“自动提取来源结构”，这为后续真正的二级权重与多标签裁决打下了地基。
