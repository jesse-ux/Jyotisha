# Antigravity AI Codex Round 30 Top 120 执行清单 (Round 29)

## Codex 立即开火 (Top 12)
1. **API 挂载 Tajika**：在 `jyotish_api_server.py` 加上 `@app.route("/api/tajika")`。
2. **API 挂载 Chara Dasha**：暴露 `/api/jaimini/chara_dasha`。
3. **前端 Varga 下拉框**：改 `main.js`，给 SVG renderer 加上 D2-D60 的 `<select>`。
4. **前端 Dasha 高亮**：给当前系统时间命中的大运加个 `class="font-bold text-red-500"`。
5. **Kuja Dosha 的 Enum**：后端废除 bool，改输出 `HIGH`, `LOW`, `CANCELLED`。
6. **Ashtakavarga 柱状图**：改 `main.js`，基于 `sav` 数据用简单的 `div` 高度画柱子。
7. **Panchanga 警告条**：如果是 Rahu Kala，在页面上方打红色 Alert。
8. **JSON Dump 按钮**：加个前端按钮触发 `JSON.stringify(data, null, 2)` 下载为 txt。
9. **`ashtakoot.py` 常量抄袭**：去 MIT 库把那 8 个矩阵的数值搬到我们的 `ashtakoot_constants.py` 里。
10. **`jyotish_engine.py --table`**：让终端极客能看到 ASCII 表格星盘。
11. **同步 SKILL**：执行 `cp SKILL.md ~/.workbuddy/...`。
12. **包裹报错**：给所有的 500 HTML 套上 `{"error": str(e)}`。

> 为什么只有这 12 个？因为在这些被 TDD 跑完之前，去写新的如 `Kalachakra Dasha` 是好高骛远，用户连现有的数据都看不到！

## 状态
`已成立`
