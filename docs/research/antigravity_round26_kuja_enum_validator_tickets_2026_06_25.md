# Antigravity AI Kuja Enum Validator 实现票据 (Round 26)

火星煞（Manglik/Kuja Dosha）不能用简单的布尔值，必须用严谨的枚举：

| 实施细则 | 代码映射与验证 |
|---|---|
| 1. 目标文件 | `scripts/oracle_evidence_validator.py` |
| 2. Enum 定义 | `["high_dosha", "low_dosha", "no_dosha", "neutralized"]` |
| 3. 校验位置 | 在读取 `ashtakoot_oracle_cases.json` 时，对 `kuja_status_boy` 和 `kuja_status_girl` 字段进行核对。 |
| 4. 报错格式 | `ValueError: Invalid kuja_status '{val}'. Must be one of {allowed}.` |
| 5. API 影响 | `/api/synastry` 返回的 JSON 里也必须使用这四个词，不能再用 `true/false`。 |
| 6. UI 影响 | 前端如果是 `high_dosha` 亮红灯，`neutralized` 亮黄灯，`no_dosha` 亮绿灯。 |
| 7. 异常测试 | 塞一个 `"kuja_status": "very_bad"` 给 validator，必须被红字拦截。 |
| 8. 豁免情况 | `neutralized` 表示原本有煞，但因为另一半也有，或者落点特殊，被抵消了。 |
| 9. Codex 任务 1 | 🟢 Codex可做 | 在 validator 中加入这 4 个词的白名单拦截 `if val not in ALLOWED:`。 |
| 10. Codex 任务 2 | 🟢 Codex可做 | 把引擎里可能还有返回 bool `True` 的地方改为 `"high_dosha"`。 |
| 11. Codex 任务 3 | 🟢 Codex可做 | 去 `jyotish-app/main.js` 里把根据 `kuja` 渲染的 `<span>` 加上对应的 CSS class (如 `.text-red-500`)。 |
| 12. 副手下轮 1 | 🟢 副手继续做 | 挖掘那多如牛毛的 `neutralized` (豁免) 古籍规则。 |
| 13. 副手下轮 2 | 🟢 副手继续做 | 给这些 Enum 加上梵文对应词 (Manglik / Anshik Manglik)。 |
| 14. 需要人工 | 🔴 否 | |
| 15. 风险 | 如果外部 Oracle 源（AstroSage）给的是百分比而不是定性，我们会很难办。 |
| 16. AstroSage 对标| 它确实是给定性的，所以该 enum 方案完美契合。 |
| 17. 为什么要改 | 占星师极其看重火星，一刀切的布尔值会被嘲笑业余。 |
| 18. 代码位置 | `_validate_synastry_evidence`。 |
| 19. Schema | string 类型的 Enum。 |
| 20. 总结 | 用强制的枚举词汇规范玄学的模糊性。 |
