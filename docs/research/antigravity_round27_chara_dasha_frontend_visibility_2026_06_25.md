# Antigravity AI Chara Dasha 前端可见性复核 (Round 27)

| 复核项 | 状态与描述 |
|---|---|
| 1. 后端可用性 | 🟢 `chara_dasha.py` 已有计算。 |
| 2. API 返回情况 | 🟡 混合状态。可能包含在全盘 JSON 或是独立的输出，但确认后端支持。 |
| 3. 前端可见性 | 🔴 前端完全不可见。`main.js` 里画的大运树 (`renderDashaTree` 类似的方法) 死死绑定了 Vimshottari。 |
| 4. UI 缺口 | 缺少一个切换按钮。用户需要看 Jaimini 流派时无从下手。 |
| 5. 交互设计 | 在大运树组件的最上方，加两个 Toggle 按钮：`Vimshottari (Nakshatra)` 和 `Chara (Rashi)`。 |
| 6. 数据结构 | Chara Dasha 也是嵌套的树状时间轴（主运 -> 副运），现有的展开折叠 DOM 代码完全可以复用。 |
| 7. 符号差异 | Vimshottari 用星体名字 (Sun, Moon)，Chara 用星座名字 (Aries, Taurus)。前端渲染无需在意，反正都是字符串。 |
| 8. 默认选中 | 永远默认选中 Vimshottari（大众标准）。 |
| 9. Codex 任务 1 | 🟢 Codex可做 | 确认 `/api/chart` 的 payload 里是否已经夹带了 `chara_dasha` 对象，若无则加上。 |
| 10. Codex 任务 2 | 🟢 Codex可做 | 在前端 `main.js` 生成一段包含两个选项卡的 `<div class="tabs">`。 |
| 11. Codex 任务 3 | 🟢 Codex可做 | 修改渲染树的代码，使其接收数据源参数，而不是写死 `data.vimshottari`。 |
| 12. 副手下轮 1 | 🟢 副手可做 | 查证 JHora 在 Chara Dasha 的输出格式，确认起止年份是否有细微容差。 |
| 13. 副手下轮 2 | 🟢 副手可做 | 在知识库里补充 Jaimini 流派的基础概念，写入悬浮提示。 |
| 14. 人工 | 🔴 否 | |
| 15. 开发成本 | 极低，因为复用树形组件。 |
| 16. 高级用户 | 非常讨好那些看不起基础算法的老手占星师。 |
| 17. 性能 | 因为只是切换内存里的 JS 对象渲染，瞬间完成。 |
| 18. 测试 | Playwright 点一下那个 tab，看有没有出现 Aries 等字样。 |
| 19. 边界情况 | Chara Dasha 也必须支持 `start_year` 的配置（如果能配置的话）。 |
| 20. 总结 | 别让绝妙的后端算法烂在字典里。 |
