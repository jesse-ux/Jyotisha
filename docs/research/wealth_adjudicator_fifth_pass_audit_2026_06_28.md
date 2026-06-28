# Wealth Adjudicator Fifth-Pass Audit (2026-06-28)

> 目标：让 `source_diversity` 不再只是 metadata，而是真正进入 finance adjudicator 的二级权重。

---

## 1. 本轮完成了什么

上一轮我们已经让 promise folding engine 开始输出：

- `primary_source`
- `supporting_sources`
- `count`
- `source_diversity`

但那时还存在一个明确边界：

> 来源结构已经进入主链，  
> 但来源结构的权重还没有进入主链。

本轮做的就是把这个边界往前推半步：

- 当 `wealth_promise_strength.source_diversity >= 2`
- 给 finance adjudicator 一个 **克制的 +5 bump**

这个 bump 的设计目标不是直接改变 verdict 档位，  
而是让系统开始承认：

> 多来源财富 promise，比单一路径重复命中更可信一些。

---

## 2. 本轮加权策略

当前实现非常保守：

```text
if wealth_promise_diversity >= 2:
    score += 5
```

特点：

1. **只做小幅加权**
2. **不直接修改 verdict 逻辑**
3. **不引入新的 overclaim 风险**

也就是说，这一步不是为了“更容易跳高分”，  
而是为了让多来源 promise 的结构价值开始被分数承认。

---

## 3. 回归结果

### 3.1 单一路径 promise

输入：

- `wealth_promise_strength.level = strong`
- `source_diversity = 1`
- `supporting_sources = ["dhana"]`

输出：

- `score = 60`
- `verdict = moderate_probability_window`

### 3.2 多路径 promise

输入：

- `wealth_promise_strength.level = strong`
- `source_diversity = 2`
- `supporting_sources = ["dhana", "lakshmi"]`

输出：

- `score = 65`
- `verdict = moderate_probability_window`

### 3.3 最关键的判断

这正是本轮想要的行为：

- **多路径支持被承认**
- **但不越级改 verdict**

换句话说：

> `source_diversity` 已经开始影响裁决结果，  
> 但它仍然被压在“保守的二级权重”层，而不是变成夸大承诺的捷径。

---

## 4. 为什么这一步重要

这是财富裁决器从“结构化 metadata”走向“结构化权重”的第一步。

以前：

- 只知道 promise 强不强

然后：

- 知道 promise 来自哪几路

现在：

- 不仅知道来源结构
- 还开始让来源结构轻微影响结果

这说明 adjudicator 的成长方向是健康的：

- 先识别结构
- 再让结构入分
- 最后才考虑更高层的标签表达

而不是一上来就因为多来源命中，直接跳成高承诺输出。

---

## 5. 当前仍然守住的边界

本轮虽然引入了权重，但仍然没有越界：

1. `source_diversity` 不会直接让 `moderate` 跳成 `high`
2. `liquidity_cashout` 仍然没有被放开
3. `Yogi` 仍然没有被假装接入
4. `dominant label + secondary context` 仍然没有草率上线

这说明当前推进还是在“硬度增长”，不是在“膨胀功能表”。

---

## 6. 下一轮最值钱的动作

如果继续按 ROI 排序，下一轮最值钱的是：

1. 接一个**轻量但真实**的 `Yogi` promise hook
   - 不重做整套 Yogi engine
   - 只接能结构化、能回归、能解释的财富正向信号
2. 再决定是否把：
   - `primary_source`
   - `source_diversity`
   - `count`
   进一步做成更细的二级权重
3. 然后才考虑：
   - `dominant label`
   - `secondary context`

---

## 7. 本轮状态判断

本轮可以诚实宣称：

- `source_diversity` 已不再只是记录项
- 它开始真实影响 finance adjudicator 分数
- 且这种影响被严格控制在“小幅 bump、不改 verdict 档位”的边界内

但还不能宣称：

- promise source weighting 已经成熟封顶
- `Yogi` 已纳入主链
- 多标签财富裁决已经完成

更准确的说法是：

> 财富 adjudicator 已进入第五阶段：  
> 来源结构不仅被识别，而且开始小幅进入权重层。  
> 这使 promise folding engine 第一次从“知道结构”成长为“让结构影响结果”。
