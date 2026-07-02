# Event Judgment Skeleton v1.0

> 用途：把分散在 `full-reading`、`dasha`、`jaimini`、`varga`、`kp`、`shadbala`、`ashtakavarga`、`references/verified-patterns-*` 中的证据，收束成统一的事件裁决链。
> 适用：marriage / career / wealth / health / generic event verification

---

## 1. Route

不要只按触发词路由。每次先识别三件事：

1. **问题域**
   - `relationship`
   - `career`
   - `wealth`
   - `health`
   - `generic_event`
2. **任务类型**
   - `prediction`
   - `backtest`
   - `rectification_support`
   - `multi-option adjudication`
3. **目标粒度**
   - `trend`
   - `window`
   - `month_level`
   - `event_level verification`

若这三件事没有先冻结，不得继续下判。

---

## 2. Evidence Ledger

每个模块必须变成结构化证据块，而不是散乱叙述。

```json
{
  "module": "marriage_timing",
  "subtechnique": "double_transit",
  "question_domain": "relationship",
  "verdict_role": "activation",
  "signal": "supportive|mixed|contradictory|blocked",
  "strength": 0.0,
  "raw_values": {},
  "engine": "native|pyjhora|vedastro|jyotishganit",
  "ayanamsa": "lahiri",
  "node_mode": "mean|true",
  "template_id": "darakaraka_ul_spouse_depth",
  "case_ref_ids": [],
  "maturity": "complete|covered|partial",
  "notes": ""
}
```

最少要求：

- `module`
- `subtechnique`
- `verdict_role`
- `signal`
- `strength`
- `raw_values`
- `engine`
- `ayanamsa`
- `node_mode`
- `maturity`

所有涉及印度占星推运、运势解读、事件预测、流年流月、健康、搬迁、考试、
出行、出生时间校正辅助或技法可靠性判断的问题，都必须复用既有
`references/mandatory-verification-gate-protocol.md`：

- `MEVG / Global Web Evidence`：记录全球 / 全网外部资料采集、source tier、
  conflict arbitration 和未验证声明的降级。
- `Real Case Calibration`：记录真实案例参考、公开 benchmark case，或明确
  case gap。
- pure calculation exemption 只适用于纯计算、纯代码、纯项目维护或不解释运势意义的
  原始数据输出；一旦解释推运或运势意义，必须执行 MEVG 与真实案例校正。

---

## 3. Adjudication

所有事件判断必须按以下顺序：

1. **Promise**
   - 本命是否有该主题的承载力？
   - 禁止直接从 Dasha/Transit 跳到“会发生”
2. **Activation**
   - Dasha / Transit / Annual / Jaimini / KP 是否激活？
3. **Manifestation**
   - 是否足以落到现实事件，而不是只形成心理主题、机会接触或背景躁动？
4. **Timing**
   - 若 Promise + Activation + Manifestation 都成立，才进入 timing 窗口判定

### 矛盾优先级

若不同证据块冲突，按以下顺序裁决：

1. `verified pattern / benchmark`
2. `cross-system convergence`
3. `classical rule with prerequisites satisfied`
4. `single module output`

若冲突无法裁决，必须输出 `blocked`。

---

## 4. Confidence Mapping

置信度不得只按“有几个名人案例”判断，至少同时考虑以下 6 维：

1. `benchmark/case support`
2. `technique maturity`
3. `cross-system convergence`
4. `birth time precision`
5. `oracle closure status`
6. `contradiction severity`

建议映射：

- `A`：多案例 / benchmark 强支撑 + complete/covered + 多系统同向 + 参数清晰
- `B`：部分案例支撑 + 多模块同向 + 仍有轻微边界
- `C`：经典规则存在，但统计、闭环或关键层不足
- `D`：仅单一模块、关键层缺失或矛盾明显

---

## 5. Output Contract

最终输出必须包含：

1. `verdict`
2. `confidence`
3. `conflicts`
4. `Technique Audit Table`
5. `raw evidence`
6. `MEVG / Global Web Evidence`
7. `Real Case Calibration`

最小 JSON 形态：

```json
{
  "event_family": "relationship",
  "verdict": "high_probability_window|moderate_probability_window|weak_window_needs_confirmation|insufficient_evidence|blocked",
  "confidence": "A|B|C|D",
  "conflicts": [],
  "primary_drivers": [],
  "missing_evidence": [],
  "raw_evidence_refs": []
}
```

---

## 6. Hard Stops

以下任一项未满足时，不得包装成高严谨结论：

- 未显式声明 `Ayanamsa / Node mode`
- 未显式声明 `Functional Benefic/Malefic`
- timing 问题未完成 `Vimshottari + Narayana`
- 题目域分盘未展开（relationship -> D9/UL；career -> D10/A10；wealth -> D2/D11）
- 外部 oracle 未闭环却假装全局封顶
- 缺少 `Technique Audit Table`
- 缺少 `MEVG / Global Web Evidence`
- 缺少 `Real Case Calibration`
