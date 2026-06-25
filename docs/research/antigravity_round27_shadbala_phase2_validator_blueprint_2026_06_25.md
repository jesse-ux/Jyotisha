# Antigravity AI Shadbala Validator Phase 2 蓝图 (Round 27)

| 蓝图拆解项 | 规则 / 架构细节 |
|---|---|
| 1. 七曜遍历 | 必须验证 Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn，遗漏任何一个则报错。 |
| 2. 六分量验证 | 必须具有 `sthana_rupa`, `dig_rupa`, `kala_rupa`, `chesta_rupa`, `naisargika_rupa`, `drik_rupa`。 |
| 3. 非法类型 | 如果值为 `None`, `null`, `""`, `True/False`，抛出 `TypeError: Shadbala value must be float.`。 |
| 4. 负数拦截 | `if value < 0: raise ValueError(...)`。 |
| 5. 极大值拦截 (防 Virupa) | 规定单项上限：`if value > 20.0: raise ValueError(...)`。 |
| 6. 总分存在性 | 必须具有 `total_rupa` 字段。 |
| 7. 总和容差 | `sum(六分量)` 与 `total_rupa` 之间的差异 `abs(diff) > 0.05` 则报 `SumMismatchError`。 |
| 8. 缺项降级 | 如果有些 Oracle (比如某网站) 就是不给 Drik，允许通过配置 `ignore_missing_components=True` 放行，但抛出 Warning。 |
| 9. 测试名 1 | `test_shadbala_validator_rejects_string_values()` |
| 10. 测试名 2 | `test_shadbala_validator_rejects_negative_rupas()` |
| 11. 测试名 3 | `test_shadbala_validator_rejects_values_above_20_rupas()` |
| 12. 测试名 4 | `test_shadbala_validator_rejects_sum_mismatch_beyond_tolerance()` |
| 13. Codex 任务 1 | 🟢 Codex可做 | 在 `oracle_evidence_validator.py` 补充上述条件。 |
| 14. Codex 任务 2 | 🟢 Codex可做 | 在 `test_oracle_evidence_validator.py` 实现上述测试。 |
| 15. Codex 任务 3 | 🟢 Codex可做 | 确保原来 JSON 里填着 `{}` 的假数据仍然被视为 `valid_packets = 0`，但不要直接让整个脚本 `sys.exit(1)`。 |
| 16. 副手下轮 1 | 🟢 副手可做 | 调研 BPHS 里 Naisargika (自然力量) 的理论最大常数是多少，看能否把 20.0 收紧到 1.5。 |
| 17. 副手下轮 2 | 🟢 副手可做 | 调研是否需要增加 Ishta Phala 的校验位。 |
| 18. 需要人工 | 🔴 否 | |
| 19. 重要性 | 这是量化占星的最深水区，绝不能让人工录入污染了测试靶标。 |
| 20. 前置条件 | `dasha_shadbala_oracle_cases.json` 的结构已定。 |
| 21. 代码位置 | `_validate_shadbala_evidence` 方法。 |
| 22. 异常栈 | 报错必须写清楚是哪颗星星、哪个分量错了。 |
| 23. 容差来源 | JHora 和我们的 Ayanamsa 若差几角秒，可能会引起边界分数略微浮动，0.05 够了。 |
| 24. 单位统一 | 强制要求用 Rupa (1 Rupa = 60 Virupa)。 |
| 25. 总结 | 用法制代替人治。 |
