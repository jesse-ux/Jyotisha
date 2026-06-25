# Antigravity AI Shadbala 七曜六分量强校验黑盒复核 (Round 18)

| 检查项 | 结论 | 证据/说明 |
|---|---|---|
| 1. 是否存在 `SHADBALA_REQUIRED_PLANETS` | 🔴 未成立 | 源码内未检出该常量。 |
| 2. 是否存在 `SHADBALA_REQUIRED_COMPONENTS` | 🔴 未成立 | 源码内未检出该常量。 |
| 3. 七曜是否包含 Sun~Saturn | 🔴 未成立 | 没有强制星球列表。 |
| 4. 六分量是否包含 sthana~drik | 🔴 未成立 | 测试中有断言，但源码未拦截。 |
| 5. 空 `{}` 是否拦截 | 🔴 未成立 | validator 会直接放行空字典。 |
| 6. 只填 Sun 两项是否拦截 | 🔴 未成立 | 校验缺失。 |
| 7. 只填 Sun 是否拦截 Moon 缺失 | 🔴 未成立 | 校验缺失。 |
| 8. 完整七曜六分量是否通过 | 🟢 已成立 | json 中存在的数据正常解析。 |
| 9. `reject_global_shadbala_scaling` | 🟢 已成立 | 已被独立测试覆盖。 |
| 10. API 层是否复用同一 validator | 🟢 已成立 | `/api/oracle_evidence` 确实调用了同套验证器。 |
| 11. 错误信息是否适合前端阅读 | 🔴 部分成立 | `missing_shadbala_component` 可读性尚可，但目前未被触发。 |
| 12. 是否纳入单位/格式校验 | 🔴 需要 | 下一步需要校验 Rupa 或百分比格式。 |

**落地建议**：Codex 需在 `scripts/oracle_evidence_validator.py` 补充针对 `SHADBALA_REQUIRED_COMPONENTS` 的深度递归判定。
