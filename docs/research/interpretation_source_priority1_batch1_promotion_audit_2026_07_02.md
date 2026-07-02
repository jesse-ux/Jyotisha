# Priority 1 第一批升格审计

日期：2026-07-02  
范围：`references/` 中最像“规则源头”的 30 个 priority_1 `reference_candidate` 文件。  
基线：[interpretation_source_full_classification_2026_07_02.md](interpretation_source_full_classification_2026_07_02.md)

这份审计只做分级，不直接接入 runtime source pack。后续真正升格时，还需要 source-pack 显式调用链、冲突仲裁、可见性测试，以及必要的 oracle / MEVG / real-case 校准。In short: promotion still requires tested wiring, not just a nicer label.

## 处置定义

- `promote`：可以进入下一步升格设计，作为 primary truth candidate 或 reference layer candidate。
- `reference-only`：有参考价值，但不能压过主规则源头，或需要等待权重/旧状态 reconciliation。
- `obsolete`：历史状态、旧审计、旧缺口矩阵；可保留追溯，不应进入解释主链。
- `duplicate`：与更强源头重复，后续只抽差异，不直接升格。
- `quarantine`：隐私、来源、内容移除、或案例边界不清；不得作为解释规则源。

## 汇总

| disposition | count | meaning |
|---|---:|---|
| `promote` | 16 | 第一批可进入升格候选 |
| `reference-only` | 6 | 辅助参考，暂不做主规则 |
| `obsolete` | 3 | 历史文件 |
| `duplicate` | 3 | 重复源 |
| `quarantine` | 2 | 隔离，不进主链 |

## Promote

| file | layer | reason |
|---|---|---|
| `references/argala-complete-guide.md` | reference layer | Argala/Virodha Argala 规则结构完整 |
| `references/ashtakavarga-complete-system.md` | reference layer | BAV/SAV 与 transit 评分方法需要可见 |
| `references/badhaka-obstacle-planet-guide.md` | reference layer | Badhaka lord 规则目前未充分接入 |
| `references/condition-dasha-complete.md` | reference layer | 条件大运适用性可防止单系统误判 |
| `references/divisional-chart-deep-reading.md` | primary candidate | 分盘深读支持 D10/D2/D11/D9 等硬约束 |
| `references/event_judgment_skeleton.md` | primary candidate | 与 strict workflow、MEVG、evidence ledger 一致 |
| `references/jaimini-complete-system.md` | reference layer | Jaimini Karaka/Chara/Karakamsha 可做非 Vimshottari 交叉 |
| `references/kp-astrology-complete-system.md` | reference layer | KP 可作为独立学派的事件 timing 参考 |
| `references/planetary-dignity-complete-reference.md` | primary candidate | 庙旺陷、moolatrikona、友敌关系是跨领域基础规则 |
| `references/pratyantar-calculation-guide.md` | reference layer | 子周期计算解释支持月级和事件级 timing |
| `references/retrograde-combustion-war-guide.md` | primary candidate | 逆行、燃烧、星战是跨领域修正层 |
| `references/shadbala-complete-methodology.md` | reference layer | Shadbala 方法论需要进入高严谨原始依据层 |
| `references/tajika-yoga-complete-guide.md` | reference layer | Tajika 年运需要规则可见，但不能声称完整闭环 |
| `references/transit-multi-reference-guide.md` | primary candidate | 多参考点 transit 可防止单锚点判断 |
| `references/vimshottari_dasha_guide.md` | primary candidate | Vimshottari 是 timing baseline |
| `references/prediction-boundary-protocol.md` | primary candidate | 预测精度、promise vs activation、降级边界必须显式存在 |

## Reference Only

| file | reason |
|---|---|
| `references/dasa-convergence-methodology.md` | 有价值，但包含旧 Narayana/PDF/software 状态，需要与当前实现核对 |
| `references/dasha-transit-method.md` | 有解释价值，但被 event skeleton 与 transit multi-reference 覆盖一部分 |
| `references/multi-dasha-convergence-protocol.md` | 现代评分框架，需 benchmark 支撑权重 |
| `references/varga-divisional-charts-quick-reference.md` | 快速参考，不应压过 deep reading 源头 |
| `references/yoga-strength-scoring-system.md` | 现代评分层，不能覆盖 yoga detection 真源 |
| `references/comprehensive-reading-workflow.md` | 广义流程参考，不是规则源头 |

## Duplicate / Obsolete / Quarantine

| disposition | file | reason |
|---|---|---|
| `duplicate` | `references/varga-system-quick-reference.md` | 与 deep reading 和 quick reference 重复 |
| `duplicate` | `references/yoga-list-chinese.md` | 与 machine-readable yoga rules / frontend yoga details 重复 |
| `duplicate` | `references/analysis-full-reading-v4.0.md` | 历史 full-reading workflow，与当前 strict source-pack 架构重复 |
| `obsolete` | `references/analysis-full-reading-v1.8-review.md` | 旧版 review，不应回灌主链 |
| `obsolete` | `references/audit-skill-full-test-2026-05-04.md` | 旧审计快照 |
| `obsolete` | `references/feature-gap-matrix-2026.md` | 旧缺口矩阵，后续状态可能已变化 |
| `quarantine` | `references/kp-practical-event-timing.md` | 内容已移除且有隐私保护声明 |
| `quarantine` | `references/consultation-case-library.md` | 案例库索引，需隐私/来源/MEVG 分级；不能作为规则源 |

## 下一步

第一批真正升格时建议按这个顺序：

1. 先接 `prediction-boundary-protocol`、`event_judgment_skeleton`、`planetary-dignity-complete-reference`、`retrograde-combustion-war-guide`、`transit-multi-reference-guide`。
2. 再接分盘、Dasha、Ashtakavarga、Shadbala、Tajika、Jaimini、KP 等专题 reference layer。
3. 对 duplicate 只做差异抽取；对 obsolete 只保留历史；对 quarantine 不进入 source pack。

