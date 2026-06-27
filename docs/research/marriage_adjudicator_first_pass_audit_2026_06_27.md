# Marriage Adjudicator First-Pass Audit (2026-06-27)

> 目标：把第一批婚恋事件样本从“命中率讨论”升级为“可校准的缺陷类型学”，为后续婚恋 adjudicator 调权与漏判修复提供标靶集。

---

## 1. 审计方法

本轮不再只看 `Rao 8参数命中数`，而是同时观察：

1. 旧体系婚恋评分（`verify-results-v6.1.json`）
2. 新体系婚恋事件聚合信号（`full-reading.modules.dasa_convergence.domain_activations.marriage_partnership`）
3. `Vivah Saham`
4. `Darakaraka marriage_quality_score`
5. `Upapada Lagna`

审计目标不是立刻改权重，而是先固定：

- 哪些案例属于 `Promise 弱型`
- 哪些属于 `Activation/Convergence 弱型`
- 哪些属于 `Manifestation 分层混淆型`
- 哪些属于 **`label-lift failure`**

---

## 2. 第一批标靶集

| case | real-world event type | old Rao score | promise verdict | activation verdict | manifestation verdict | formalization verdict | final adjudicator verdict | miss type | suspected missing features |
|---|---|---:|---|---|---|---|---|---|---|
| Priyanka Chopra + Nick Jonas | legal marriage | 2/8 | medium | weak (`L1`) | partial | medium | weak window / under-lifted | activation/convergence weak | Chara/Jaimini marriage activation, transit support, legal-marriage label lift |
| Britney Spears + Jason Alexander | legal marriage | 4/8 | medium | weak (`None`) | weak | weak | insufficient / weak | manifestation split unclear | short-marriage handling, unstable legal marriage tagging |
| Britney Spears + Kevin Federline | legal marriage | 7/8 | medium | weak (`None`) | medium | medium | **under-lifted** | **label-lift failure** | conversion from strong legacy score to legal-marriage event label |
| Princess Diana + Prince Charles | public formalization | 5/8 | medium | weak (`None`) | medium | strong | moderate but mis-labeled | manifestation split | public formalization vs marriage quality separation |
| Barack Obama + Michelle Robinson | legal marriage | 4/8 | medium | weak (`None`) | medium | medium | under-lifted | activation/convergence weak | Venus-type marriage activation not fully lifted |
| Tom Cruise + Katie Holmes | public formalization | 7/8 | medium | weak (`None`) | medium | strong | **under-lifted** | **label-lift failure** | public-formalization event family not surfaced |

---

## 3. 关键发现

### 3.1 主要瓶颈不在 promise，而在 event label lift

这批样本里，最显著的问题不是“完全没有婚恋结构”，而是：

- `Vivah Saham` 常常为 `high` 或 `moderate`
- `DK score` 常常在 `0.55-0.65`
- `UL` 也能给出社会表现线索
- 但 `marriage_partnership` 经常是 `None` 或仅 `L1`

这说明系统看到了一部分婚恋结构，但**没有把它抬升成正确的事件标签**。

### 3.2 `label-lift failure` 应作为独立缺陷类别

以下样本最典型：

- `Britney Spears + Kevin Federline`
- `Tom Cruise + Katie Holmes`

共同特征：

- 旧 Rao 分数高（`7/8`）
- 现实事件明确成立
- 新聚合器中的 `marriage_partnership` 仍然没有点亮

这不是传统意义上的“完全没算到”，而是一个新的、可校准的聚合器缺陷：

**旧体系能命中，但新体系没有正确抬升事件标签。**

### 3.3 “婚姻事件”需要拆成至少四层

本轮样本已支持继续沿用以下拆分：

1. `romantic activation`
2. `relationship formation`
3. `legal marriage`
4. `public formalization`

像 `Princess Diana + Prince Charles`、`Tom Cruise + Katie Holmes` 这类名人样本，很可能在第 4 层更强，而不应被粗暴等同为“高质量婚姻事件”。

---

## 4. 下一轮修复重点

1. 给 `marriage_partnership` 聚合层增加 `label-lift failure` 专门回归样本
2. 单独补“legal marriage / public formalization”事件标签
3. 将 `Vivah Saham + DK/UL + dual dasha` 的同向组合作为婚恋 lift 候选
4. 用女性样本继续扩展：
   - `relationship formation`
   - `engagement/public relationship`
   - `legal marriage`

---

## 5. 版本备注

- 本文档是第一轮审计，不是最终 benchmark
- 目的在于固定缺陷类型，而不是立即宣布婚恋 adjudicator 已完成校准
