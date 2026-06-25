# Antigravity AI 完整 Ashtakoot 引擎 Provenance 设计 (Round 23)

合婚引擎返回的数据必须向用户表明其“来源正当性”：

| 设计维度 | 计划方案 |
|---|---|
| 1. `source_project` | 在返回的 JSON 中增加：`"VedAstro"`。 |
| 2. `source_license` | 增加：`"MIT"`。 |
| 3. `algorithm_variant` | 增加：`"ashtakoot_36_point_standard"`。 |
| 4. `external_oracle_status` | 默认填 `not_external_verified`。 |
| 5. `constant_source` | 指向具体的字典，如 `scripts/ashtakoot_constants.py`。 |
| 6. `calibration_status` | 取决于 `oracle_evidence_validator` 返回的 `valid_packets`。 |
| 7. `not_external_verified` 边界 | 只要没有满 5 个真人截图包裹验证，此值永远为真。 |
| 8. Tests | 检查 `/api/synastry` 返回体内必须包含 `provenance` 对象。 |
| 9. UI 展示 | 在 36分打分表下方，用灰色小字写明：“打分常数基于 VedAstro (MIT)；本算法尚未获得 JHora 真实截图核验，请勿用于重大决策。” |
| 10. Prompt Pack | 喂给大模型的 system prompt 里直接附带 provenance 对象。 |
| 11. JSON 导出 | 当用户点击 Download 时包含进去，防止其拿半成品去行骗。 |
| 12. 最小实现 | 在 `ashtakoot.py` 的返回体 `result` 字典里挂载一个 `provenance` key。 |

**落地建议**：一旦抄录完成，立刻给它打上 MIT 和未校准的双重标记。
