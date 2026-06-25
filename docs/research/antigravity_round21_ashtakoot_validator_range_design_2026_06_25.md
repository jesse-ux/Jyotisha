# Antigravity AI Ashtakoot Validator 边界控制设计 (Round 21)

未来验证人工提交的 36 分 Ashtakoot JSON 包时，必须追加以下硬隔离校验规则：

| 校验逻辑与范围 | 预期行为 / 建议的 Error Code |
|---|---|
| 1. `total_score` 类型 | 拒绝字符串，仅支持 Float / Int。 |
| 2. `total_score` 范围 | `0 <= total_score <= 36`。 超出则 `invalid_ashtakoot_score_range:target.total_score`。 |
| 3. `varna` 分值 | `0 <= varna <= 1`。 |
| 4. `vashya` 分值 | `0 <= vashya <= 2`。 |
| 5. `tara` 分值 | `0 <= tara <= 3`。 |
| 6. `yoni` 分值 | `0 <= yoni <= 4`。 |
| 7. `graha_maitri` 分值 | `0 <= graha_maitri <= 5`。 |
| 8. `gana` 分值 | `0 <= gana <= 6`。 |
| 9. `bhakoot` 分值 | `0 <= bhakoot <= 7`。 |
| 10. `nadi` 分值 | `0 <= nadi <= 8`。 |
| 11. 8 Kuta 求和容差 | `abs(varna + ... + nadi - total_score) < 0.05`。 错误码：`ashtakoot_component_sum_mismatch`。 |
| 12. `kuja_status` 枚举 | 仅允许 `"low_risk", "medium_risk", "high_risk", "neutralized"` 或具体布尔。 |
| 13. bool/空/负数拒绝 | 空值报错 `placeholder_unfilled`。负值报错 `invalid_ashtakoot_component_negative`。 |
| 14. 超大值拒绝 | 若任何单项 > 8，触发防呆阻断。 |
| 15. 测试用例 | `test_oracle_evidence_validator.py` 补充 8 个断言。 |

**最小 Codex 改动建议**：在 `oracle_evidence_validator.py` 增加一个 `_validate_ashtakoot_components(target)` 函数，把 0-8 的字典映射写进去。
**参考文件位置**：`scripts/oracle_evidence_validator.py`
