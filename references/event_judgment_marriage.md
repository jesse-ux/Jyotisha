# Marriage Event Adjudicator v1.0

> 这是 `relationship` 题目域的专用裁决器。用于婚恋、婚姻、配偶、正式关系、关系转正、长期关系是否成立等问题。

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
3. **关系定义**
   - `legal marriage`
   - `formal partnership`
   - `sustained relationship`

若关系定义不清，先说明判定对象再继续。

---

## 2. Mandatory Layers

婚恋题目至少必须展开：

- `D1`: 7H / 7L / Venus / Jupiter / Mars / Moon / DK
- `D9`: Lagna / 7H / 7L / Venus-Jupiter / DK
- `UL`
- `Vimshottari + Narayana`
- `Transit / Double Transit`
- `Vivah Saham`
- `Functional Benefic/Malefic`

若用户要求高严谨，还应尽量加：

- `KP 7H sub-lord`
- `Chara Dasha`
- `Argala on 7H / 7L / UL`

---

## 3. Evidence Ledger Roles

把婚恋证据按 4 种角色分类：

1. `promise`
   - 7H / 7L / DK / UL / D9 是否支持婚恋承诺
2. `activation`
   - Dasha / Transit / Double Transit / KP / Saham 是否激活
3. `manifestation`
   - 这些激活是否足以落到现实关系成立，而不是只表现为暧昧、吸引、情绪事件
4. `timing`
   - 若上三层成立，再给窗口或月份级判断

---

## 4. Marriage Adjudication Order

### 4.1 Promise

先问：

- 本命是否有婚恋承载力？
- D1 的 7H / 7L / Venus / Jupiter / DK 是否形成基本 promise？
- D9 是否支持，还是明显削弱？
- UL 是否支持“正式关系/婚姻质量”？

若 promise 本身薄弱，不得直接因为某段 Dasha 激活就断定“必然结婚”。

### 4.2 Activation

必须检查：

- `Vimshottari` 是否激活 7H / 7L / Venus / Jupiter / DK / UL
- `Narayana` 是否同向
- `Transit / Double Transit` 是否对 7H / 7L / DK / UL 有作用
- `Vivah Saham` 是否支持

若 `Vimshottari` 与 `Narayana` 明显相反，标记 `mixed` 或 `blocked`。

### 4.3 Manifestation

这一层专门防止“有窗口但没落地”。

要区分：

- `romantic activation`
- `relationship formation`
- `legal marriage`
- `public formalization`

尤其对名人、公职人物、长期恋爱者，要警惕“关系已成立，但婚礼日期只是社会安排”。

### 4.4 Timing

只有在 Promise + Activation + Manifestation 都通过后，才给：

- 趋势级
- 窗口级
- 月份级
- 事件验证级

若只能做到窗口级，必须明说不能上升到“具体婚礼日”。

---

## 5. Template Hooks

优先调用并引用：

- `darakaraka_ul_spouse_depth`
- `strict-workflow-router.md` 的 `relationship-timing-strict`
- `marriage-timing-validation-methodology.md`

若调用不到，必须在 Audit Table 里标注其对置信度的削弱。

---

## 6. Output Contract

婚恋输出最少要有：

1. `relationship verdict`
2. `confidence`
3. `main conflicts`
4. `Technique Audit Table`
5. `raw evidence`

示例 verdict：

- `high_probability_window`
- `moderate_probability_window`
- `weak_window_needs_confirmation`
- `insufficient_evidence`
- `blocked`

---

## 7. Must-Not-Overclaim

以下情况必须降级或阻断：

- 只看 `Vimshottari` 没看 `Narayana`
- 只看 `DK` 没看 `UL/D9`
- 只看 `Double Transit` 就断婚期
- 只看单一文章规则
- 未说明 birth time precision
- 未说明 `Ayanamsa / Node mode`
