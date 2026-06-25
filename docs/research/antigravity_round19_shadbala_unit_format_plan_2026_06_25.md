# Antigravity AI Shadbala 单位格式下一轮校验方案 (Round 19)

| 校验维度 | 当前方案缺陷 | 下一轮补强计划 (Round 20) |
|---|---|---|
| 1. 结构检查 | 目前只查是否为空或缺 Key。 | 保持现状，这是极好的第一道门禁。 |
| 2. 数据类型 | 允许字符串如 `"100.5"` 或 `"100"`。 | 必须在 `oracle_evidence_validator.py` 强化：拒绝 string，强制要求 JSON `float` 或 `int`。 |
| 3. Rupa/Virupa | JHora 显示的往往是 Virupa 或 Rupa 小数点。 | 要求用户一律按 Rupa 小数填写（如 `6.25` 而非 `375`），并在 Guide 里增加说明。 |
| 4. 负数处理 | 未拦截。 | Shadbala 力量绝不可能为负，应抛出 `invalid_shadbala_range` 错误。 |
| 5. 极端大数 | 未拦截。 | 任何单项力量超过 20 Rupa 明显属于用户填错，应告警。 |
| 6. Component Sum | 未校验加总。 | 应当校验 `sthana + dig + kala + chesta + naisargika + drik` 的求和是否接近 `total`，以防漏写。 |
| 7. JHora 显示差异 | JHora 的 % 与 Rupa 共存。 | 必须在 JHora Capture Guide 里贴一张图，圈出“取这列小数点数值，不取百分比”。 |
| 8. 必须进入 Round 20 | 🟡 是。 | 否则用户随便填个 `"abc"` 就能骗过系统升为 `external_verified`。 |

**落地建议**：在 Round 20，`oracle_evidence_validator.py` 必须引入 `isinstance(val, (int, float))` 以及 `val >= 0` 的校验拦截。
