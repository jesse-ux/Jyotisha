# Antigravity AI 前端全技能暴露度审计 (Round 24)

| 技能项 | 前端可见状态 | 差距或判定 |
|---|---|---|
| 1. D1 盘 | 可见 | UI 完整 |
| 2. D9 盘 | 可见 | UI 完整 |
| 3. D10 盘 | 可见 | UI 完整 |
| 4. 剩余 13 种 Varga | 不可见 | 仅在 CLI/API 返回，UI 无按钮 |
| 5. Vimshottari Dasha | 可见 | UI 完整，可展开 3 层 |
| 6. Yogini Dasha | 不可见 | API 支持，UI 未画表 |
| 7. Shadbala | 可见 | 雷达图显示 |
| 8. Yoga | 可见 | 在 `Yogas & Special Interpretations` 列表 |
| 9. Ashtakavarga | 部分可见 | 仅在 Yoga 里提及 337 总分，无独立点阵图 |
| 10. Ashtakoot | 可见 | 关系合盘页面 |
| 11. Tajika | 不可见 | API 支持计算，但无年份输入 UI |
| 12. 来源/置信度 | 缺失 | 整个星盘页面未见“未通过截图认证”字样 |
| 13. 移动端拥挤度 | 部分拥挤 | Dasha 树在小屏下很难点 |
| 14. Demo 按钮 | 存在 | Export 里的 calibration 弹窗目前全灰 |
| 15. 下一轮 UI 建议 | 优先 | 将其余 13 个分盘塞进一个折叠的 `More Vargas` 里 |
| 16. E2E 缺口 | 严重 | 没有通过 Playwright 测试所有面板的显隐 |

**副手下一轮任务**：设计 D2 财帛盘和 D3 兄弟盘在移动端的排版方案。
**Codex 可做任务**：在 `main.js` 里接上 Yogini Dasha 的数据并用普通的 `<table>` 渲染出来。
