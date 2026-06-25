# Antigravity AI Kuja Status 枚举与叠加设计 (Round 22)

在印度合婚中，Kuja Dosha（火星煞）至关重要。

| 设计维度 | 计划方案 |
|---|---|
| 1. `kuja_status` 允许值 | `["no_dosha", "mild_dosha", "strong_dosha", "neutralized"]`。 |
| 2. 区分等级 | 是的。不同的宫位（如第 8 宫和第 2 宫）煞气强弱不同。 |
| 3. 双方各自状态 | 是的。输入时必须知道 Male 和 Female 各自是否带煞。 |
| 4. 进入 36 分？ | 🔴 **不**！它是在 36 分之外独立的“一票否决”或“减分惩罚”机制。 |
| 5. 作为 Flag 独立存在 | 🟢 是的。在最终判定 `verdict` 时综合考量。 |
| 6. 对标工具输出 | JHora 和 AstroSage 在 Ashtakoot 旁边必有 `Manglik Match` 的独立大字。 |
| 7. Validator 错误码 | `invalid_kuja_status_enum:target.kuja_status`。 |
| 8. UI 展示 | 在 36 分表格下方放一个 `🔥 火星煞状态` 警告条。 |
| 9. Tests | 增加枚举值越界验证用例。 |
| 10. 与 `mangal_dosha` 关系 | 复用目前的单人 `mangal_dosha` 判断结果，合盘只做 A + B 的组合逻辑。 |
| 11. 等待外部 oracle | 是的。先别自己拍脑袋写叠加规则，看看 AstroSage 怎么消煞（Neutralized）。 |
| 12. 最小实现建议 | `scripts/oracle_evidence_validator.py` 加上一个只允许上述 4 个字符串的拦截。 |

**最小 Codex 改动建议**：在 `oracle_evidence_validator.py` 中为 `target.kuja_status` 新增枚举集合校验。
