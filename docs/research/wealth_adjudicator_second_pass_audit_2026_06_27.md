# Wealth Adjudicator Second-Pass Audit (2026-06-27)

> 目标：在第一轮 `public_wealth_status` 护栏落地后，继续修复财富裁决器的两个核心问题：  
> 1. `wealth promise strength` 没有入分  
> 2. `income_growth` 与 `public_wealth_status` 仍会互相吞并

---

## 1. 本轮修复点

本轮没有继续扩新标签，而是只做两件事：

1. **把 `wealth_promise_strength` 接入 finance adjudicator 显式计分**
   - `strong` -> `+20`
   - `moderate` -> `+10`
2. **增加 `income_growth` 优先分流**
   - 当 `gains_convergence` 很强
   - 且 `wealth/career` 公众财富信号不够强
   - 则优先落 `income_growth`

这意味着财富裁决器不再只看：

- `wealth_convergence`
- `gains_convergence`
- `career_convergence`
- `dual dasha`

而开始把“本命财富 promise”当成正式入分项。

---

## 2. 新增回归边界

本轮新增并跑通两条主仓回归测试：

1. `Britney-like`  
   目标：当收益爆发明显高于公众财富身份信号时，应更偏 `income_growth`
2. `Rihanna-like`  
   目标：当 `wealth promise strength = strong` 时，允许从第一轮的 under-lift 状态被抬升到更合理的 `public_wealth_status`

---

## 3. Before / After

| case | first-pass outcome | second-pass outcome | change |
|---|---|---|---|
| Britney-like breakout income growth | `moderate_probability_window` + `public_wealth_status` | `moderate_probability_window` + `income_growth` | 修复了标签误吸收，收益爆发不再被误说成公众财富身份 |
| Rihanna-like commercial empire visibility | `weak_window_needs_confirmation` 或依赖外层 workaround | `moderate_probability_window` + `public_wealth_status` | 通过 `wealth_promise_strength` 显式入分，终于能把强财富 promise 兑现到标签层 |

---

## 4. 关键结论

### 4.1 `wealth promise strength` 已经从“解释层概念”进入“裁决层分数”

这是本轮最值钱的变化。

之前：

- `Lakshmi / Dhana / Yogi` 模板更多停留在解释和研究文档里
- finance adjudicator 不真的把它们当分数

现在：

- `wealth_promise_strength` 已成为显式计分输入

虽然它还不是最终形态，但财富裁决器已经开始真正吸收本仓现成的财富 promise 资产。

### 4.2 `income_growth` 和 `public_wealth_status` 第一次开始分家

第一轮护栏虽然堵住了“弱窗口乱贴公众财富标签”，但 `Britney-like` 仍会被误贴成 `public_wealth_status`。

第二轮后：

- `Britney-like` -> `income_growth`
- `Rihanna-like` -> `public_wealth_status`

这说明财富 adjudicator 不再把所有“财富变好”都说成同一种事。

### 4.3 `Rihanna-like` 终于从“强样本漏判”进入“可校准命中”

第一轮里最刺眼的问题是：

- `Rihanna` 这种 textbook 级商业财富样本
- 竟然还抬不起来

现在这条样本第一次被 `wealth promise strength` 正式救活。  
这说明问题的确不是“标签词库不够”，而是 promise 分没进来。

---

## 5. 当前仍未完成的部分

本轮虽然把骨架往前推了一截，但还没有结束：

1. `wealth_promise_strength` 现在还是一个抽象输入，尚未从完整 `full-reading.modules.yogas_doshas + template hooks` 自动汇总
2. `Lakshmi / Dhana / Yogi` 还没有全部自动折叠成统一 promise 指标
3. `liquidity_cashout` 依然没有建立独立 uplift 逻辑
4. `public_wealth_status` 与 `asset_accumulation` 还没有完全分开

---

## 6. 下一轮最值钱的动作

下一轮不该再泛泛讨论“财富准不准”，而应直接做这三件事：

1. 从 `full-reading.modules.yogas_doshas.dhana_yogas` 自动提取 `wealth_promise_strength`
2. 把 `lakshmi_dhana_activation_chain` / `yogi_asc_tight_orb_wealth` 接成真实 promise hook，而不是手工传入
3. 增加 `asset_accumulation` vs `public_wealth_status` 的回归样本

---

## 7. 本轮状态判断

本轮可以诚实宣称：

- 财务裁决器已经不再只是 convergence + dasha 的薄聚合器
- 本命财富 promise 已开始进入显式计分
- `income_growth` 与 `public_wealth_status` 已出现第一层真实分流

但还不能宣称：

- 财富 adjudicator 已经完整封顶
- Lakshmi / Dhana / Yogi 已经全部自动闭环进裁决器

更准确的说法是：

> 财富 adjudicator 已经从“行为护栏阶段”进入“财富 promise 真正入分阶段”，  
> 并开始具备区分收益爆发与公众财富身份的裁决能力。
