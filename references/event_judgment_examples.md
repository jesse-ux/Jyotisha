# Event Judgment Examples v1.0

> 作用：给事件判定骨架提供最小可执行范例，避免只停留在抽象规则。

---

## 示例一：婚恋窗口判断

### 问题

`When will I get married?`

### Route

- question_domain: `relationship`
- task_type: `prediction`
- target_granularity: `window`

### Evidence Ledger（最小示例）

```json
[
  {
    "module": "relationship_timing",
    "subtechnique": "d9_ul_dk",
    "question_domain": "relationship",
    "verdict_role": "promise",
    "signal": "supportive",
    "strength": 0.82,
    "raw_values": {"d9": "present", "ul": "present", "dk": "present"},
    "engine": "native",
    "ayanamsa": "lahiri",
    "node_mode": "mean",
    "template_id": "darakaraka_ul_spouse_depth",
    "case_ref_ids": ["marriage-timing-v6"],
    "maturity": "covered",
    "notes": ""
  },
  {
    "module": "relationship_timing",
    "subtechnique": "dual_dasha",
    "question_domain": "relationship",
    "verdict_role": "activation",
    "signal": "supportive",
    "strength": 0.78,
    "raw_values": {"vimshottari": "Venus/Rahu", "narayana": "Pisces/Jupiter"},
    "engine": "native",
    "ayanamsa": "lahiri",
    "node_mode": "mean",
    "template_id": "darakaraka_ul_spouse_depth",
    "case_ref_ids": [],
    "maturity": "covered",
    "notes": ""
  }
]
```

### Adjudication

- Promise: pass
- Activation: pass
- Manifestation: partial
- Timing: window only

### Output Contract

```json
{
  "event_family": "relationship",
  "verdict": "moderate_probability_window",
  "confidence": "B",
  "conflicts": [],
  "primary_drivers": ["d9_ul_dk", "dual_dasha"],
  "missing_evidence": ["kp_7h_sub_lord"],
  "raw_evidence_refs": ["full-reading.modules.jaimini.darakaraka", "full-reading.modules.dasa_convergence"]
}
```

---

## 示例二：财富窗口判断

### 问题

`When will my wealth grow?`

### Route

- question_domain: `wealth`
- task_type: `prediction`
- target_granularity: `window`

### 关键约束

- 必须 `D2 / D11`
- 必须 `Vimshottari + Narayana`
- 必须 `Shadbala + Ashtakavarga`
- 若缺任一核心层，直接降为 `insufficient_evidence`

---

## 示例三：过去事件回测

### 问题

`Was my 2018 relationship event actually supported by the chart?`

### Route

- question_domain: `relationship`
- task_type: `backtest`
- target_granularity: `event_level verification`

### 输出要求

- 不只说“像不像”
- 必须输出 `A / B / C / Fail`
- 必须指出是 Promise 不足、Activation 不足，还是 Manifestation 不足
