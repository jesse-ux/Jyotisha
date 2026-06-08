# Jyotish benchmark 第六轮补充：Ashtakavarga 表级口径仲裁

生成时间：2026-06-03

## 1. 仲裁目的

- 第六轮图表输出对标显示：当前 skill 与 PyJHora 的 BAV/SAV 不完全一致。
- 本轮不再比较具体命盘，而是直接比较两边的 BAV 贡献表定义，判断差异是运行 bug 还是表级口径差异。
- 样本与表格均不包含用户个人资料。

## 2. 固定总分校验

| Planet | Expected | Local total | Local valid | PyJHora total | PyJHora valid | Delta |
|---|---:|---:|---|---:|---|---:|
| Sun | 48 | 48 | True | 48 | True | 0 |
| Moon | 49 | 49 | True | 49 | True | 0 |
| Mars | 39 | 39 | True | 39 | True | 0 |
| Mercury | 54 | 54 | True | 54 | True | 0 |
| Jupiter | 56 | 56 | True | 56 | True | 0 |
| Venus | 52 | 52 | True | 52 | True | 0 |
| Saturn | 39 | 39 | True | 39 | True | 0 |
| Lagna | 49 | 49 | True | 49 | True | 0 |

## 3. 总量对比

| Metric | Local skill | PyJHora table | Expected |
|---|---:|---:|---:|
| 7-planet SAV table total | 337 | 337 | 337 |
| Full table total incl. Lagna | 386 | 386 | 386 |

## 4. 不一致的贡献表项

共 0 个 planet/source 表项不一致。

| Planet BAV | Source | Local houses | PyJHora houses | Missing in PyJHora | Extra in PyJHora |
|---|---|---|---|---|---|

## 5. 仲裁结论

- 当前 skill 与 PyJHora `const.ashtaka_varga_dict` 的贡献表项已 100% 对齐。
- 两边均满足 Ashtakavarga 固定总量不变量：7行星 SAV=337，含 Lagna full total=386。
- 决策：第六轮初始差异已由 v2.1 表项校准修复，Ashtakavarga 表定义层通过。
- 后续若引入其他软件对标，必须先比较贡献表项和 SAV 总量，不得直接把口径差异判为运行 bug。

## 6. 对第六轮状态的影响

- Ashtakavarga 计算层：当前 skill 内部不变量通过，可暂列为“默认 BPHS v2.0 口径通过”。
- 与 PyJHora 的差异：降级为“外部引擎表口径差异”，不作为 P0/P1 bug。
- 解释层使用要求：输出 Ashtakavarga 时应声明使用 BPHS v2.0/SAV=337 口径。