# Antigravity AI Prompt Pack 引入 Progress 的用户价值复核 (Round 20)

| 检查项 | 结论 | 证据/说明 |
|---|---|---|
| 1. CLI JSON | 🟢 已成立 | `full-reading` 返回的 JSON 已挂载了 `oracle_progress`。 |
| 2. API JSON | 🟢 已成立 | `/api/chart` 的 `ai_prompt_pack.evidence_snapshot` 中已包含该字段。 |
| 3. 前端 fallback | 🟢 已成立 | Web 前端组装 fallback 时已补上了 `valid_packets: 0`。 |
| 4. Chat buildReadingPrompt | 🟢 已成立 | 在发送给大语言模型前，`valid_packets: 0` 的上下文会被拼进去。 |
| 5. evidence copy | 🟢 已成立 | 用户点击复制证据时能带上。 |
| 6. retrieval tags | 🟢 已成立 | 已打上 `external_oracle_evidence_validation` tag。 |
| 7. 避免误称校准 | 🟢 已成立 | LLM 看到 0/5 和 tuning_allowed=false 后，不会信口开河。 |
| 8. token 成本 | 🟢 可控 | 仅增加约 20 个 token。 |
| 9. 适合展示给用户 | 🟢 极好 | 用户发现 AI 说“我们还在收集外部样本阶段”会觉得非常极客且真实。 |
| 10. Ashtakoot 也要加？ | 🟡 需要 | 未来 Ashtakoot 做 36分对标时，也该把 `ashtakoot_progress` 加给大模型。 |

**落地建议**：本次 Codex 把 progress 嵌入 Prompt Pack 堪称神来之笔。它让基于这个项目打包的 AI Agent 瞬间具有了“自身仍在研发迭代期”的意识。
