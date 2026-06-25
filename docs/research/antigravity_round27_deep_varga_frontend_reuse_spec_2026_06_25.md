# Antigravity AI 深分盘前端复用规格 (Round 27)

我们的引擎里有非常全的 Varga (D1 到 D60)，但前端只有 D1 和 D9 并列。大师们要看 D10, D30, D60 怎么办？

| 规格要求 | 实施细节 |
|---|---|
| 1. 后端支持度 | 🟢 `divisional.py` 或类似模块中包含所有的 D 盘度数切分算法，且随 `/api/chart` 下发了字典。 |
| 2. 前端 SVG 器 | 🟢 现有的 `renderChartSVG(divId, chartData, 'south/north')` 之类的函数，目前写死了 D1 和 D9 的提取逻辑。 |
| 3. 复用改造点 | 提取 SVG 画图逻辑，使其变成 `renderChartSVG(domNode, specificVargaData, style)`。 |
| 4. UI 布局 | 在原本只显示 D9 的那个盒子的左上角，放一个 `<select class="varga-selector">`。 |
| 5. 下拉菜单项 | `<option value="D9">D9 (Navamsha - 婚姻/灵魂)</option>` `<option value="D10">D10 (Dashamsha - 事业)</option>` `<option value="D60">D60 (Shashtiamsha - 前世/潜意识)</option>`。 |
| 6. 交互事件 | `select.addEventListener('change', (e) => { 拿到选中的 varga_key，重新调 renderChartSVG 画进去 })`。 |
| 7. 响应式 | 在手机上这极大地节约了空间，不用把所有图全平铺。 |
| 8. 默认态 | 页面刷新时，默认展示 D9。 |
| 9. Codex 任务 1 | 🟢 Codex可做 | 把 `main.js` 里写死的 `render(D9_div, data.d9)` 改造为事件监听回调驱动。 |
| 10. Codex 任务 2 | 🟢 Codex可做 | 在 HTML 里写死那个 `<select>`，或者用 JS 动态插入选项。 |
| 11. Codex 任务 3 | 🟢 Codex可做 | 确保 `/api/chart` 确实吐出了全套的 varga 数据，不要遗漏 D2, D3, D4, D7, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60。 |
| 12. 副手下轮 1 | 🟢 副手可做 | 给每一个 D 盘配上一句英文简述（如 D2 = Wealth），放进前端的常量表。 |
| 13. 副手下轮 2 | 🟢 副手可做 | 审查 D60 的分割算法是否与 JHora 的 Parashara 派系完全一致。 |
| 14. 人工 | 🔴 否 | |
| 15. ROI | 极高，只需不到 50 行 JS 代码，直接解锁十几个高阶占星图表。 |
| 16. 图表样式 | 无论是南印还是北印风格，该方案都能完美兼容。 |
| 17. 性能 | 因为坐标数据已经随首次 API 下发，切换下拉框属于 0 延迟。 |
| 18. UX 体验 | 可以给下拉框加个微弱的闪光提示用户“这里可以点”。 |
| 19. PWA | 非常符合移动端的操作直觉。 |
| 20. 总结 | 这是让我们的 App 看上去极其专业的捷径。 |
