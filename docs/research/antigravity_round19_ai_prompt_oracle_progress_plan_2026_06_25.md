# Antigravity AI Prompt Pack 引入 Oracle 进度的建议 (Round 19)

| 检查项 | 结论 | 证据/说明 |
|---|---|---|
| 1. 当前包含 oracle progress | 🔴 否 | 目前的 `ai_prompt_pack` 尚未将 progress dashboard 的状态打包装入。 |
| 2. 包含 Dasha/Shadbala 边界 | 🟢 是 | `SKILL.md` 中已经写了不许说满话，这是 Prompt 之外的系统级护栏。 |
| 3. 包含 `valid_packets: 0` | 🔴 否 | 后端并没有实时把这个数值塞进给大模型的 `evidence_snapshot` 中。 |
| 4. 包含 `tuning_allowed` | 🔴 否 | 同上。 |
| 5. 写入 retrieval plan | 🟡 强烈建议 | AI 如果知道 `references/oracle/artifacts/` 正在召集截图，可以主动在聊天中教用户怎么截图发 PR！ |
| 6. 写入 external_verified 规则 | 🟡 强烈建议 | 让大模型在遇到疑问时主动回答：“受限于 0/5 的外部证据，目前的绝对值不可信”。 |
| 7. 避免误导已校准 | 🟢 已成立 | `SKILL.md` 中严禁。 |
| 8. 修改文件建议 | 🟡 行动点 | `scripts/jyotish_engine.py` 在拼接 `ai_prompt_pack` 时，去读取一下 progress 的 JSON，加到 `evidence_snapshot` 中。 |
| 9. 测试建议 | 🟡 行动点 | `test_frontend_productization.py` 添加针对 Prompt 包含 `valid_packets` 的断言。 |
| 10. 用户价值 | 🟢 极高 | 让 AI 变成一个带有自省能力、主动号召开源共建的推销员。 |

**落地建议**：下一轮让 Codex 在生成 AI Prompt 的时候，把 `valid_packets` 的整数嵌进去，这相当于赋予了 AI “知晓自身项目阶段”的超能力。
