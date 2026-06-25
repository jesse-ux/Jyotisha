# Antigravity AI Shadbala Validator 二期验收设计 (Round 25)

由于 Shadbala 的值很容易被输入错（Virupa 经常大到几百，Rupa 通常在 4~10 之间），我们需要对 `oracle_evidence_validator.py` 下狠手：

| 校验层 | 验收标准与防御逻辑 |
|---|---|
| 1. 数据类型 (Schema) | `sthana`, `dig`, `kala`, `chesta`, `naisargika`, `drik` 必须全提供。 |
| 2. 单位控制 (Unit) | 全部强制视作 Rupa。如果有任何一个分量 > 20.0，判定为 Virupa 错填，拦下报错 `invalid_shadbala_component_too_large`。 |
| 3. 单项范围 (Range) | 每颗星（Sun-Saturn）各项必须在 `(0.0, 20.0)` 这个 tuple 范围内。 |
| 4. 总分求和验证 (Tolerance)| 所有 6 项加起来，必须等于 `total_score`，容许有 `0.05` 的浮点舍入误差。 |
| 5. Minimum Bala | 根据古籍，总 Rupa 一般在 `4.0 ~ 12.0` 间，若算出 `< 1.0` 可能是计算黑洞，抛出警告但可不拦截。 |

**副手下一轮任务**：为上述 5 条规则准备 3 个会导致触发报错的伪造 JSON，测试拦截效果。
**Codex 可做任务**：去 `oracle_evidence_validator.py` 增加一个 `SHADBALA_COMPONENT_MAX_RUPA = 20.0` 的变量并加上 for 循环拦截。
**Codex 可做任务 2**：写一个 `abs(sum(components) - total) > 0.05` 的拦截语句。
