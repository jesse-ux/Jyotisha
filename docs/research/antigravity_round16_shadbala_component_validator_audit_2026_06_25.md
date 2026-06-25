# Antigravity AI Shadbala 六分量强校验复核 (Round 16)

我们在 `oracle_evidence_validator.py` 中要求，若 `targetFields` 中包含 `shadbala_components`，必须递归核查内部所有子项。以下是目前拦截防线的审计结果：

| 规则 | 是否检查 | 缺口 | 推荐修复 |
|---|---|---|---|
| `sthana` | 🔴 否 | 仅存在于测试和 mock case 里，真正的 validator 对其睁一只眼闭一只眼。 | 在 validator 的 `target` 检查块内硬编码写死这 6 个 key 的必填校验。 |
| `dig` | 🔴 否 | 同上 | 同上 |
| `kala` | 🔴 否 | 同上 | 同上 |
| `chesta` | 🔴 否 | 同上 | 同上 |
| `naisargika`| 🔴 否 | 同上 | 同上 |
| `drik` | 🔴 否 | 同上 | 同上 |

**结论**：Codex 在本轮 **尚未实现** 对 `shadbala_components` 六分量的底层强校验阻击。目前只要有这个空字典就能蒙混过关。
