# Antigravity AI Shadbala 单位/总分强校验二期 (Round 21)

| 校验维度 | 二期强化计划 |
|---|---|
| 1. Rupa vs Virupa | 只接受 Rupa，由于 Virupa 通常是 Rupa 的 60 倍，我们设置所有分量的上限必须 < 20。 |
| 2. 是否必须保存 `unit` | 不需要，在填写 JSON 时强制要求就是 Rupa。 |
| 3. sum 与 total 关系 | 各项相加的误差不能超过 0.1。 |
| 4. 七曜 total 必填 | `oracle_evidence_validator.py` 中必须强制要求含有 `total` 字段。 |
| 5. 每一分量合理上限 | `sthana`, `dig`, `kala`, `chesta`, `naisargika`, `drik` 无论如何不可能超过 20 Rupa。 |
| 6. 错误码 | 新增 `invalid_shadbala_component_too_large`。 |
| 7. 截图读数不清 | 若提供图片模糊导致总分对不上，执行退回流程。 |
| 8. 小数容差 | `abs(sum - total) < 0.1` 即可放行。 |
| 9. Validator 测试 | `test_oracle_evidence_validator.py` 补充 2 个针对总分的断言。 |
| 10. API 上传错误 | 同一暴露给前端，翻译成“总分不匹配”的中文红灯。 |
| 11. UI 展示 | 在填写页提示“所有分项之和必须近似等于 Total”。 |
| 12. 是否阻塞 1/5 | 🟢 是的。如果首个验证包乱写数据，会直接被阻断，不予通过 1/5 晋级。 |

**最小 Codex 改动建议**：在 `oracle_evidence_validator.py` 中，遍历所有的 `planet.components` 时，顺手计算一个总和，与 `total` 做比对。
