# Antigravity AI AI Prompt Pack / Skill 同步复核 (Round 18)

| 检查项 | 状态 | 结论与证据 |
|---|---|---|
| 1. `ai_prompt_pack` 后端是否输出 | 🟢 已成立 | `full-reading` 接口的最新文档中明确有该字段。 |
| 2. 前端是否可复制 Prompt | 🟢 已成立 | `main.js` 包含“AI Prompt Pack 审计上下文已复制”弹窗。 |
| 3. 前端是否可复制 Evidence | 🟢 已成立 | 包含 `evidence_snapshot`。 |
| 4. Prompt 是否包含 4 项证据快照 | 🟢 已成立 | D1/D9/Dasha/Shadbala/Ashtakavarga 结构被整合进快照。 |
| 5. 是否提示外部校准边界 | 🟢 已成立 | `SKILL.md` 中严厉要求 AI 不得把 Dasha/Shadbala 绝对值说成已完成校准。 |
| 6. Skill 文档是否同步这些边界 | 🟢 已成立 | `SKILL.md` 包含 `ready_for_calibration: 0` 和 `valid_packets: 0` 的上下文。 |
| 7. API bridge 是否同步 | 🟢 已成立 | `/api/thematic_report` 等已挂载。 |
| 8. 是否存在夸大准确率话术 | 🟢 未检出 | `SKILL.md` 已修改为保守话术。 |
| 9. 是否需要加入 oracle progress 摘要 | 🟡 需要 | AI 在解读时应该知道目前正处于外部样本募集期，甚至可以邀请懂占星的用户帮忙。 |
| 10. 是否需要加入 license 摘要 | 🟡 需要 | 声明基础排盘来源于 pyswisseph。 |
