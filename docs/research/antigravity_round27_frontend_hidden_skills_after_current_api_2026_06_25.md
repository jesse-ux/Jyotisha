# Antigravity AI 前端隐藏技能 ROI 重排 (Round 27)

基于前后端代码分析，这些技能已经在后端甚至 API 层面就绪，但用户在界面上“无处可点”：

| 排名 | 前端未表现技能 | 现状 / 实现方案 | 商业 ROI |
|---|---|---|---|
| 1 | Panchang & Muhurta | API `/api/panchanga_range` 已有。前端仅剩一行字。方案：画个月历表。 | 极高（高频刚需）。 |
| 2 | Chara Dasha | `/api/chart` 里可能有或很快有。方案：在 Dasha 面板旁边加个 Tab。 | 高（高级玩家必备）。 |
| 3 | 深分盘 (D7/D60 等) | `/api/chart` 已返回数据。方案：在 D9 SVG 旁边加个下拉框，一键重绘 SVG。 | 高（零后端修改即可实现巨大体验升级）。 |
| 4 | Tajika 年运盘 | 后端 `varshaphala.py` 有。方案：主页加个 `Target Year` 选框，跳转新面板。 | 高（年度复购）。 |
| 5 | Ashtakavarga 细节 | API 有数据。方案：在现有的 Yoga 下方画个 12 格子的分值图。 | 中（进阶用户）。 |
| 6 | KP 强弱表 | 后端已有。方案：列表展示 249 sublord 映射。 | 中。 |
| 7. | Codex 任务 1 | 🟢 Codex可做 | 在 UI Dasha 模块增加一个按钮切换 Vimshottari 与 Chara。 |
| 8. | Codex 任务 2 | 🟢 Codex可做 | 提取目前死绑 D1/D9 的画图逻辑，使之接受 `selected_varga` 参数。 |
| 9. | Codex 任务 3 | 🟢 Codex可做 | 在 SVG 上方画个 `<select id="varga-selector">`，包含 D1 到 D60。 |
| 10. | 副手下轮 1 | 🟢 副手可做 | 学习 D30 和 D60 的特定占星用途，给下拉框配上注释 (如 D60: 前世)。 |
| 11. | 副手下轮 2 | 🟢 副手可做 | 画 Ashtakavarga 12 宫图的 CSS Grid 结构体。 |
| 12. | 人工 | 🔴 否 | |
| 13. | 技术债 | 我们的前端渲染目前太 hardcode 了。 |
| 14. | 复用性 | SVG renderer 是我们的神兵利器，必须榨干它的价值。 |
| 15. | PWA | 考虑到移动端，下拉框比密密麻麻的单选按钮好。 |
| 16. | UI 库 | 没有使用 React，纯 Vanilla JS，所以更新 DOM 时小心内存泄漏。 |
| 17. | 测试 | 改完前端后，一定要跑 Playwright 截屏测试。 |
| 18. | 性能 | 都在内存里重绘，不用重新请求 API。 |
| 19. | 竞品 | AstroSage 有所有的分盘。 |
| 20. | 总结 | 这叫“用前端的一小步，换取功能的一大步”。 |
