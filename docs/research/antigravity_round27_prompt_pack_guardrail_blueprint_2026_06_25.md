# Antigravity AI Prompt Pack 解盘护栏蓝图 (Round 27)

| 蓝图拆解项 | 规则 / 架构细节 |
|---|---|
| 1. 不铁口直断 | `pytest` 检查生成的 Prompt 是否强制含有 `"禁止使用绝对的字眼（如必然、一定）"`。 |
| 2. 不夸大准确率 | 检查 Prompt 是否含有 `"不要夸大我们的计算精准度，明确声明缺乏外部校准"`。 |
| 3. 不做医疗建议 | 检查 Prompt 是否含有 `"禁止给出任何具体的医学、疾病治疗或用药建议"`。 |
| 4. 不做金融承诺 | 检查 Prompt 是否含有 `"禁止给出具体的投资买卖指示"`。 |
| 5. 不做法律建议 | 检查 Prompt 是否含有 `"禁止对官司输赢做确切保证"`。 |
| 6. 必须引用证据 | 检查 Prompt 是否含有 `"请务必在你的推断后面加上括号，注明是哪颗星/哪个宫位支撑的该论点"`。 |
| 7. 动态免责注入 | 在 `/api/chart` 组装 AI Prompt 的那一刻，把这些强硬约束拼接到 System Message 末尾。 |
| 8. 代码注入点 | `scripts/prompt_generator.py` (或者在 main engine 拼接的地方)。 |
| 9. 前端渲染同步 | 生成的证据对象 (evidence_snapshot) 必须作为 payload 发给大模型。 |
| 10. 测试名 1 | `test_prompt_generation_includes_medical_and_financial_guardrails()` |
| 11. 测试名 2 | `test_prompt_generation_mandates_evidence_citation()` |
| 12. 测试名 3 | `test_prompt_generation_warns_against_absolute_predictions()` |
| 13. Codex 任务 1 | 🟢 Codex可做 | 用 `pytest` 创建 `tests/test_prompt_security.py`。 |
| 14. Codex 任务 2 | 🟢 Codex可做 | 在业务逻辑里把护栏字眼写死。 |
| 15. Codex 任务 3 | 🟢 Codex可做 | 跑通断言。 |
| 16. 副手下轮 1 | 🟢 副手可做 | 整理一批典型的“用户钓鱼式提问”用于日后大模型评测。 |
| 17. 副手下轮 2 | 🟢 副手可做 | 给这些护栏加上英文对照，以便发送给英文大模型。 |
| 18. 需要人工 | 🔴 否 | |
| 19. 为什么要做 | 我们不能因为大模型胡说八道而承担项目声誉受损的风险。 |
| 20. 底层信任 | 只有护栏足够高，用户才敢信。 |
| 21. Schema | 这是 Prompt Engineering 的一部分，不是算法，但要用 TDD 保证它没被弄丢。 |
| 22. AI 回复检查 | 目前我们还没法在后端做正则拦截，所以只能在 Prompt 端下重手。 |
| 23. OpenAI 策略 | 这是符合 OpenAI 商业化应用准则的标准做法。 |
| 24. P0 级别 | 这是上线商用前绝对的 P0。 |
| 25. 总结 | 用测试代码去约束自然语言。 |
