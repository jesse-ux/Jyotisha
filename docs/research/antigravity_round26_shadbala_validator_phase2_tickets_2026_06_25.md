# Antigravity AI Shadbala Validator 二期实现票据 (Round 26)

为了杜绝在人工敲击 Oracle 数据时填出天方夜谭的数字：

| 实施细则 | 数据限制与代码位置 |
|---|---|
| 1. 目标文件 | `scripts/oracle_evidence_validator.py` |
| 2. 字段限制 | 所有的 `xxx_rupa` (比如 `kala_rupa`)。 |
| 3. 单位转换 | 所有的 Rupa 都必须是 `float`，不可是 String。 |
| 4. 上限控制 | 单项必须 `<= 20.0`。一旦 > 20，直接判定是在乱填 Virupa。 |
| 5. 下限控制 | 单项必须 `>= 0.0`。不可能是负数。 |
| 6. 精度容差 | `total_score` 必须等于 6 项分量之和，考虑到浮点，`abs(sum - total) <= 0.05`。 |
| 7. 拦截抛错 | `ValueError: Shadbala component {key} exceeds Rupa limit (20.0). Did you enter Virupas by mistake?` |
| 8. 错误码定义 | 增加一种 `ShadbalaUnitError`。 |
| 9. 测试用例 1 | 给出一个单项为 `350` 的错误 JSON，断言被拦截。 |
| 10. 测试用例 2 | 给出一个总和算错的 JSON，断言被拦截。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 在 validator 的 `_validate_shadbala_evidence` 函数里写入上限控制代码。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 在 validator 加上浮点求和比对逻辑。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 跑一遍该脚本确保原来的模板数据不报错。 |
| 14. 副手下轮 1 | 🟢 副手继续做 | 查证 BPHS 典籍，看看太阳的 Kala Bala 理论上最高能达到多少 Rupa，以微调 20.0 这个天花板。 |
| 15. 副手下轮 2 | 🟢 副手继续做 | 将这套校验逻辑扩展到后续可能加入的 `Ishta Phala` 等参数。 |
| 16. 需要人工 | 🔴 否 | |
| 17. 为什么要做 | 因为 Virupa 经常被小白抄错成 Rupa，差了 60 倍。 |
| 18. 安全边界 | 这只是一个校验器，不会影响实际的计算引擎逻辑。 |
| 19. 兼容性 | 旧的 0/5 空模板数据默认被跳过，不会崩。 |
| 20. 总结 | 严防死守外部垃圾数据污染我们的测试地基。 |
