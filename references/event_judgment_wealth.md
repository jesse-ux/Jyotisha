# Wealth Event Adjudicator v1.0

> 这是 `wealth` 题目域的专用裁决器。用于收入、财富积累、到账、套现、资产扩张、估值跃升、公众财富地位等问题。

---

## 1. Route Freeze

先冻结三件事：

1. **任务类型**
   - `prediction`
   - `backtest`
   - `rectification_support`
   - `multi-option adjudication`
2. **目标粒度**
   - `trend`
   - `window`
   - `month_level`
   - `event_level verification`
3. **财富事件标签**
   - `income_growth`
   - `asset_accumulation`
   - `liquidity_cashout`
   - `public_wealth_status`

若财富事件标签不清，先说明判定对象再继续。

---

## 2. Four Wealth Layers

财富题目固定拆成四层：

1. `wealth promise`
2. `wealth activation`
3. `wealth manifestation`
4. `payout label`

### payout label 子类

- `income_growth`：收入增长、薪资提升、持续现金流增强
- `asset_accumulation`：资产沉淀、持仓扩大、房产/股权/长期财富积累
- `liquidity_cashout`：到账、套现、融资落袋、出售变现
- `public_wealth_status`：IPO、估值跃升、财富排行榜、公众财富可见度

---

## 3. Mandatory Layers

财富题目至少必须展开：

- `D1`: 2H / 11H / 5H / 9H / 10H / Jupiter / Venus / Mercury
- `D2`
- `D11`
- `D10`（若财富来自职业兑现）
- `Vimshottari + Narayana`
- `Shadbala`
- `Ashtakavarga`
- `Functional Benefic/Malefic`
- `MEVG / Global Web Evidence`
- `Real Case Calibration`

高严谨时尽量补：

- `Argala on 2H / 11H`
- `A2 / A11 / A10`
- `KP`
- `Yogi / Dhana / Lakshmi template hooks`

---

## 4. Evidence Ledger Roles

把财富证据按 4 种角色分类：

1. `promise`
   - 本命是否具备财富承载力或财富兑现潜力？
2. `activation`
   - Dasha / Transit / Annual / KP / Jaimini 是否点燃财富主题？
3. `manifestation`
   - 这些激活是否足以落到现实收益/资产/现金流，而不只是机会、焦虑或纸面波动？
4. `payout_label`
   - 最终更像哪一类财富事件：收入增长、资产积累、套现到账、公众财富地位？

---

## 5. Wealth Adjudication Order

### 5.1 Promise

先问：

- 2H / 11H / 5H / 9H / 10H 是否给出财富承诺？
- D1 的财富 promise 是否得到 `D2 / D11 / D10` 支持？
- Jupiter / Venus / Mercury 在题目域里是增强器、兑现器还是干扰器？
- 是否存在强财富模板钩子：
  - `lakshmi_dhana_activation_chain`
  - `yogi_asc_tight_orb_wealth`

若本命 promise 薄弱，不得因为单次 transit 或单个 Dasha 就断定“发财”。

### 5.2 Activation

必须检查：

- `Vimshottari` 是否激活 2L / 11L / 5L / 9L / 10L / Jupiter / Venus / Mercury
- `Narayana` 是否同向
- `Transit Jupiter / Saturn / nodes` 是否对 2H / 11H / 10H 有实质推动
- `Shadbala / Ashtakavarga` 是否支持“强而可兑现”的状态

若 `Vimshottari` 与 `Narayana` 明显冲突，标记 `mixed` 或 `blocked`。

### 5.3 Manifestation

这一层专门防止“有财运感，但没落到现实收益”。

要区分：

- `opportunity to earn`
- `actual income growth`
- `asset build-up`
- `cash-out / liquidity event`
- `public wealth visibility`

### 5.4 Payout Label

只有前三层通过后，才给最终财富事件标签。

禁止把所有财富事件都压成一个粗糙的“发财”。

---

## 6. Defect Typology

财富线沿用婚恋线的缺陷类型思路：

1. `promise weak`
2. `activation/convergence weak`
3. `manifestation split`
4. `payout-label failure`

### payout-label failure

定义：

- 旧体系高分
- 现实财富事件明确成立
- 新聚合器没有把它抬成正确的财富标签

这是财富线最重要的回归靶子之一。

---

## 7. Template Hooks

优先调用并引用：

- `lakshmi_dhana_activation_chain`
- `yogi_asc_tight_orb_wealth`
- `strict-workflow-router.md` 的 `wealth-timing-strict`
- `divisional-chart-deep-reading.md` 中的财富链 `D2 -> D4 -> D10 -> D11`

若调用不到，必须在 Audit Table 里标注其对置信度的削弱。

---

## 8. Output Contract

财富输出最少要有：

1. `wealth verdict`
2. `confidence`
3. `main conflicts`
4. `Technique Audit Table`
5. `raw evidence`
6. `MEVG / Global Web Evidence`
7. `Real Case Calibration`

`MEVG / Global Web Evidence` 必须复用
`references/mandatory-verification-gate-protocol.md`，至少说明 source tier、
global web evidence collection、conflict arbitration 和未验证声明如何降级。

`Real Case Calibration` 必须给出真实案例参考、公开 benchmark case，或明确的
case gap。没有可比案例时不得假装完成，应降低置信度。

pure calculation exemption 只适用于纯计算、纯代码、纯项目维护或不解释运势意义的原始
数据输出；一旦解释财富运势、收入窗口、到账、资产或变现，必须执行 MEVG 与真实案例校正。

示例 verdict：

- `high_probability_window`
- `moderate_probability_window`
- `weak_window_needs_confirmation`
- `insufficient_evidence`
- `blocked`

最终还要给出：

- `payout_label`

---

## 9. Must-Not-Overclaim

以下情况必须降级或阻断：

- 只看 `Vimshottari` 没看 `Narayana`
- 只看 `D1` 没展开 `D2 / D11`
- 把事业曝光误当成财富兑现
- 把纸面估值误当成流动性到账
- 未说明 birth time precision
- 未说明 `Ayanamsa / Node mode`
- 未完成 `MEVG / Global Web Evidence`
- 未完成 `Real Case Calibration`
