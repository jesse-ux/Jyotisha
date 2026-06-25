# Antigravity AI Round 24 Ashtakoot 误判纠正报告 (Round 25)

| 检查项 | 核查状态 | 事实依据与说明 |
|---|---|---|
| 1. "全是0"是否成立 | 🔴 误判已纠正 | `calculate_ashtakoot(0,0)` 返回 28.0，不是全 0。 |
| 2. 哪些返回非零 | 🟢 已成立 | Varna, Vashya, Tara, Yoni, GrahaMaitri, Gana, Bhakoot, Nadi 全都有非零分数。 |
| 3. 常量矩阵存在 | 🟢 已成立 | 源码内含有 `VASHYA_MATRIX`, `YONI_ENEMIES`, `GANA` 等矩阵字典。 |
| 4. 不像 JHora 输出处 | 🟡 部分成立 | 我们还没加入 D9 (Navamsa) 等更复杂的附加 Kuta，分数粒度可能偏粗。 |
| 5. Oracle 0/5 意味 | 🔴 未成立 | 即使我们有分，因为没有截取 JHora 进行校验，我们不能宣称计算 100% 同步。 |
| 6. Round 24 误导文件 | 🟢 已成立 | `antigravity_round24_codex_round25_implementation_backlog` 中要求“从 VedAstro 抄数据”是建立在“我们全为0”的错觉上的。 |
| 7. 立即重写 ashtakoot? | 🔴 未成立 | 不需要。我们的常数表可能已经比较齐了，现在需要的是调优而不是全盘推翻。 |
| 8. 加 provenance/progress?| 🟢 已成立 | 迫在眉睫。把 0/5 状态抛给用户和 AI 才是最诚实的。 |
| 9. 最小修复任务 | 🟢 Codex可做 | 把 Round 24 中过激的“全是0”注释从脑海中删掉，检查我们现在的字典和 VedAstro 到底差几条。 |
| 10. 测试任务 | 🟢 Codex可做 | 为每一项 Kuta 编写特定的正交测试用例，比对 AstroSage 结果。 |
| 11. UI 提示任务 | 🟢 已成立 | 在前端 Trust Center 展示 0/5。 |
| 12. README 边界任务 | 🟢 已成立 | 声明合婚还未过外部验证。 |
| 13. 外部采样任务 | 🟢 需人工外部工具 | 从 AstroSage 或 JHora 上搞定那 5 个 JSON！ |
| 14. license 风险 | 🟢 已成立 | 只要常量是用 MIT 的，就没风险。 |
| 15. 用户体验风险 | 🟢 已成立 | 没有免责条框就是最大的风险。 |
| 16. 下一轮计划 | 🟢 副手继续做 | 把我们的常量表和 VedAstro 的常数进行按格 diff 审计。 |
| 17. 可复制命令 | 🟢 成立 | `python3 -c "from scripts.ashtakoot import calculate_ashtakoot; print(calculate_ashtakoot(0,60))"` |
| 18. 最终判定 | 🟢 成立 | 彻底推翻了前两轮的“合婚系统仍在返回全 0”的谬论，恢复代码名誉。 |
