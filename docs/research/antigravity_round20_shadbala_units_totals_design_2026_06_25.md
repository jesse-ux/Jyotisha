# Antigravity AI Shadbala 单位与总分设计 (Round 20)

| 设计维度 | 下一轮补强建议 (Round 21) |
|---|---|
| 1. Rupa/Virupa 字段 | 应当要求一律换算为 **Rupa** (比如 6.25)，禁止混填 Virupa (375)。 |
| 2. 是否允许百分比 | 严禁填入百分比（如 `120%`）。在 `oracle_evidence_validator.py` 中拒绝带 `%` 的值。 |
| 3. Component Sum | 验证器中新增：如果所有分量加起来与提供的 `total` 误差超过 0.1 Rupa，抛出警告。 |
| 4. 浮点容差 | PyJHora 和 JHora 可能存在 0.01 级别的四舍五入差异。对标时采用 `abs(a - b) < 0.05`。 |
| 5. JHora 读取位置 | JHora 在 `Strengths` -> `Shadbala` 表格中，第一行数字即 Rupa。在 Guide 里截图画红圈。 |
| 6. PyJHora 读取 | 从 stdout 解析 `Rupas` 列。 |
| 7. Validator 变更 | `scripts/oracle_evidence_validator.py` 继续增加 `invalid_shadbala_component_range`。 |
| 8. API/UI 错误展示 | 目前返回 400 会带着 `problems` 数组，前端会自动画成红灯。继续复用。 |
| 9. 测试用例 | 在 `test_oracle_evidence_validator.py` 加一个填了 `150.0` 超大数字被拦截的断言。 |
| 10. 是否进入 Round 21 | 🟡 视情况。如果人类填的首个包顺利，可以稍微放宽；否则必须加上防错阈值。 |

**落地建议**：在 `oracle_evidence_validator.py` 补充一个极端值预警：当任何一个单项得分 > 20 Rupa 时，直接报错。这能有效拦截那些填错 Virupa (几百) 的人。
