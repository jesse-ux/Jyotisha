# Career Event Adjudicator v1.0

> 这是 `career` 题目域的专用裁决器。用于职位变动、项目落地、晋升、事业突破、公众职业状态与职业兑现窗口等问题。

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
3. **事业事件标签**
   - `career_status`
   - `role_change`
   - `promotion_window`
   - `project_manifestation`

若事业事件标签不清，先说明判定对象再继续。

---

## 2. Mandatory Layers

事业题目至少必须展开：

- `D1`: 10H / 10L / Sun / Saturn / Mercury / Jupiter
- `D10`
- `A10 / Karma Pada`
- `Jaimini`: `AmK / AK / Karakamsha`
- `Vimshottari + Narayana`
- `Transit / Double Transit`
- `Shadbala`
- `Functional Benefic/Malefic`
- `MEVG / Global Web Evidence`
- `Real Case Calibration`

高严谨时尽量补：

- `Argala on 10H / 10L / A10`
- `Kakshya`
- `KP`
- `Ashtakavarga`

---

## 3. Evidence Ledger Roles

把事业证据按 4 种角色分类：

1. `promise`
   - 本命是否具备事业承载力、职位成长性、社会可见度？
2. `activation`
   - Dasha / Transit / Jaimini / KP 是否点燃事业主题？
3. `manifestation`
   - 这些激活是否真正落到职位变化、项目落地、职业兑现？
4. `label`
   - 最终更像哪类事业事件：职业状态、角色变化、升迁窗口、项目兑现？

---

## 4. Career Adjudication Order

### 4.1 Promise

先问：

- 10H / 10L / Sun / Saturn / Mercury 是否给出事业承诺？
- `D10` 是否支持，还是削弱？
- `A10 / Karma Pada` 是否支持社会职业显现？
- `AmK / Karakamsha` 是否支持职业兑现？

若本命 promise 薄弱，不得因为短期 transit 或单段 Dasha 就断定“事业必成”。

### 4.2 Activation

必须检查：

- `Vimshottari` 是否激活 10H / 10L / Sun / Saturn / Mercury / A10 / AmK
- `Narayana` 是否同向
- `Transit / Double Transit` 是否对 10H / 10L / A10 有推动
- `Argala / Kakshya / Ashtakavarga` 是否提供支持或阻力

若 `Vimshottari` 与 `Narayana` 明显冲突，标记 `mixed` 或 `blocked`。

### 4.3 Manifestation

这一层专门防止“有事业感，但没落到现实兑现”。

要区分：

- `career pressure / preparation`
- `role change`
- `project manifestation`
- `public career status`

### 4.4 Label

只有前三层通过后，才给最终事业事件标签。

禁止把所有事业事件都压成一个粗糙的“事业好”。

---

## 5. Template Hooks

优先调用并引用：

- `strict-workflow-router.md` 的 `career-timing-strict`
- `transit-actionable-output-guide.md`
- `divisional-chart-deep-reading.md` 中的 `D10`
- `jaimini-complete-system.md`

若调用不到，必须在 Audit Table 里标注其对置信度的削弱。

---

## 6. Output Contract

事业输出最少要有：

1. `career verdict`
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
数据输出；一旦解释事业运势、职业窗口、项目落地或职位变化，必须执行 MEVG 与真实案例校正。

示例 verdict：

- `high_probability_window`
- `moderate_probability_window`
- `weak_window_needs_confirmation`
- `insufficient_evidence`
- `blocked`

最终还要给出：

- `dominant_label`

---

## 7. Must-Not-Overclaim

以下情况必须降级或阻断：

- 只看 `Vimshottari` 没看 `Narayana`
- 只看 `D1` 没展开 `D10 / A10`
- 把职业曝光误当成实质职位兑现
- 没交代 `AmK / Karakamsha`
- 未说明 birth time precision
- 未说明 `Ayanamsa / Node mode`
- 未完成 `MEVG / Global Web Evidence`
- 未完成 `Real Case Calibration`
