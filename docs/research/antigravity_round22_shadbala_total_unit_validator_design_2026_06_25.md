# Antigravity AI Shadbala 总分/单位二期复核设计 (Round 22)

| 设计维度 | 计划方案 |
|---|---|
| 1. Schema: totals | 增加 `target.shadbala_totals: [float]` 来存放总分。 |
| 2. Schema: unit | 只接受 `Rupa`。不要写 Virupa，免得一会乘 60 一会除 60。 |
| 3. Rupa/Virupa 选择 | 一律强制使用 Rupa。 |
| 4. component sum vs total | 各分项求和，必须与输入的 total 进行比对。 |
| 5. 每分项上限 | `sthana`, `dig` 等每一项不可超过 20 Rupa。 |
| 6. 每总分上限 | 七曜的总分最高大概是 10-15 Rupa，所以设置 20 Rupa 绝对足够。超过的，必是填错了单位（Virupa）。 |
| 7. 容差 | 由于舍入误差，允许差值 `0.1`。 |
| 8. 截图读法 | JHora 里的数字，有些是带小数的 Rupa，有些是百分比，必须教会用户读取倒数第三行或 Rupa 的那行。 |
| 9. 错误码 | `shadbala_score_sum_mismatch` 或 `invalid_shadbala_component_too_large`。 |
| 10. Tests | 至少准备 2 个总分和上限相关的测试。 |
| 11. 阻塞 1/5 | 🟢 必须！填错 Virupa 就不配晋级。 |
| 12. 最小实现 | 在 `oracle_evidence_validator.py` 里拦截大于 20 的分量即可。 |

**落地建议**：通过对总分和上限的封锁，我们能保证录入的数据质量是纯正的 Rupa。
