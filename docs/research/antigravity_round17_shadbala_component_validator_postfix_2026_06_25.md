# Antigravity AI Shadbala 六分量强校验修复后复核 (Round 17)

通过对验证器及其测试用例的代码检索和运行，我们发现 Shadbala 的子项强校验依然存在断层：

| 规则 | 是否检查 | 证据 token | 仍有缺口 |
|---|---|---|---|
| `sthana` | 🔴 否 | 仅存于 tests，无 validator 源码 | 未成立 |
| `dig` | 🔴 否 | 仅存于 tests，无 validator 源码 | 未成立 |
| `kala` | 🔴 否 | `missing_shadbala_component:Sun.kala` 仅在 test 内 | 未成立 |
| `chesta` | 🔴 否 | `missing_shadbala_component:Sun.chesta` 仅在 test 内 | 未成立 |
| `naisargika`| 🔴 否 | `missing_shadbala_component:Sun.naisargika` 仅在 test 内 | 未成立 |
| `drik` | 🔴 否 | `missing_shadbala_component:Sun.drik` 仅在 test 内 | 未成立 |
| `空 {}` | 🔴 否 | 未被拦截 | 未成立 |
| 本地引擎拦截 | 🟢 是 | `status_not_external_verified:draft` | 已成立 |

**复现命令与检查点**：
1. 检查测试脚本：`rg "missing_shadbala_component" tests/test_oracle_evidence_validator.py` 有内容。
2. 检查验证源码：`rg "sthana|dig|kala|chesta|naisargika|drik" scripts/oracle_evidence_validator.py` **结果为空**。
3. 检查空括号：当前用例仍未阻挡空字典。
4. 本地输出拦截：在 `python3 scripts/oracle_evidence_validator.py --queue-file ...` 结果中可见拦截。

**修复建议**：Codex 必须在 `scripts/oracle_evidence_validator.py` 中写死包含这 6 个 key 的 `SHADBALA_REQUIRED_COMPONENTS`，并对 `targetFields.shadbala_components` 里的各个星体展开递归校验。

*(此测试无须人工截图介入)*
