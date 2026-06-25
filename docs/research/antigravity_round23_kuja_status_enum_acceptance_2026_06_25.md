# Antigravity AI Kuja Status Enum 验收细化 (Round 23)

| 验收维度 | 细化标准 |
|---|---|
| 1. 允许值 | 严格限定为：`no_dosha`, `mild_dosha`, `strong_dosha`, `neutralized`。 |
| 2. Validator 错误码 | 抛出 `invalid_kuja_status_enum:target.kuja_status`。 |
| 3. UI 文案 | `no_dosha` -> 无火星煞；`strong_dosha` -> 严重火星煞。 |
| 4. 测试样本 | 针对包含和不包含在枚举中的字符串写 `test_validator_rejects_invalid_kuja_status`。 |
| 5. 与 `calc_kuja_dosha` | 我们本身在星盘模块有火星落 1,2,4,7,8,12 宫的判定逻辑。合婚里的状态，是基于男女双盘的判定进行互相抵消后的结果（即 `neutralized`）。 |
| 6. 是否入总分 | 不入。这独立于 36分。 |
| 7. AstroSage 兼容 | AstroSage 给出的是 Manglik Match 状态，我们需让人工录入时将其映射到上述 4 个词。 |
| 8. 最小修复 | 在 `oracle_evidence_validator.py` 里新增该字段的 `in` 判断。 |

**落地结论**：此 Enum 控制是为了让合婚验证包不再只有数值，还要具有定性状态。
