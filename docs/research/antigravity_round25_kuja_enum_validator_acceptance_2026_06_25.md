# Antigravity AI Kuja Validator 验收设计 (Round 25)

目前火星煞 (Kuja Dosha) 作为一个非常关键的布尔值/枚举，绝不能混入 Ashtakoot 36 分。

| 设计项 | 说明与实施 |
|---|---|
| 1. Enum 集合 | `"high_dosha"`, `"low_dosha"`, `"no_dosha"`, `"neutralized"` (被豁免)。 |
| 2. 报错码 | 如果 JSON 中给出了其他词（比如 "true", "yes"），报错 `invalid_kuja_enum`。 |
| 3. 测试样本 | 找两个都是 `high_dosha` 的盘，验证合盘接口应当给出“煞气互相抵消”的提示。 |
| 4. AstroSage 接口 | AstroSage 对于火星煞是单独给出一个弹框，我们照做。 |
| 5. 为什么不打分 | 火星如果在 1,4,7,8,12 宫，它直接一票否决，不会换算成 36 分里的某 2 分。 |
| 6. 前端 UI | UI 里加个小火星图标，如果无 Dosha 就绿色，有就深红。 |
| 7. 下一步 Codex 1 | 🟢 Codex可做 | 在 `oracle_evidence_validator.py` 里拦截不是这 4 个词的 `kuja_status`。 |
| 8. 下一步 Codex 2 | 🟢 Codex可做 | 在 `jyotish_engine.py` 里针对火星落宫，简单用 if/else 返回这四种 enum。 |
| 9. 下一步 副手 | 🟢 副手继续做 | 挖掘 BPHS 中关于火星如果落在特定星座（如巨蟹）就可以豁免（neutralized）的极其复杂的例外表。 |
| 10. 需要人工 | 🔴 否 | |
