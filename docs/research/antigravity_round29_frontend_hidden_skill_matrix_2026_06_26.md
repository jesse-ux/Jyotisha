# Antigravity AI 前端隐藏技能总表 (Round 29)

## 页面展现僵局

`jyotish-app/main.js` 目前硬编码了 D1 和 D9 的渲染，且没有导航切换结构。导致大量 API 已下发的数据成为暗物质。

1. **分盘库 (`vargas`)**：
   API `chart` 里其实带有 D2, D3, D10 等数据，但前端无下拉框。加一个 `<select id="varga-select">` 就能激活。
2. **Ashtakavarga (八字分)**：
   JSON 里有 `sav`, `bav`，但没画出 12 宫的得分表。这是一个 `<table>` 就能解决的事。
3. **Chara Karakas (Jaimini 指标)**：
   AK, AmK 等指标在 `planets` 数组里有标注，但前端列表里没有这个列。
4. **Tara Bala**：
   吉日推算里有这个值，没在日历呈现。
5. **Dasha 三级展开**：
   目前的大运是一坨大表，应该做成 `<details><summary>` 那种折叠树。
6. **Yoga 的吉凶高亮**：
   只是纯文本列出了 Yoga，没有用 CSS `bg-red-100` 或 `bg-green-100` 区分。

## 状态
`部分成立`
