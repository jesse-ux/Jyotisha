# Antigravity AI 前端产品化冲刺 Top 50 (Round 28)

一切不长在界面上的功能都是耍流氓。

## 界面扩展行动项

1. **导航栏重构**：从单一页面变成多 Tabs：`Birth Chart` | `Panchang & Muhurta` | `Match Making` | `Prashna (Horary)` | `Yearly (Tajika)`。
2. **Panchang 交互图**：用 Tailwind 网格画出日历，红色标示 Rahu Kala。
3. **深分盘切换**：在 D9 SVG 上方加一个 Select，包括 D1 到 D60。
4. **Dasha 切换**：增加 Vimshottari / Chara Dasha 切换开关。
5. **KP / Sublord 视图**：设计紧凑的表格展示 Planets 和 Houses 的 SL/SSL。
6. **火星煞警示**：用橙红绿展示 Kuja Dosha 的 Enum 状态，加说明提示框。
7. **合婚雷达图**：8 个 Kuta 的得分用 8 边形雷达图画出，直观显示哪里短板。
8. **Yoga / Dosha 面板**：列出所有命中的格局，加星标表示吉，骷髅标表示凶。
9. **导出 PDF 优化**：使用 `html2pdf.js` 把页面样式一键保存为精美 PDF 报告。
10. **Ayanamsa 全局设置**：在右上角加齿轮图标，允许用户切换 Lahiri, Raman 等。
11. **离线 PWA 支持**：利用 Service Worker 缓存计算引擎 JS。
12. **AI 解盘对话框**：不再是生成一堆长文，而是类似 ChatGPT 的聊天气泡，允许追问。
13. **免责声明常驻**：用温馨的淡黄色条幅，把“AI 不是神仙，本软件算法未作终极对标”挂在前头。

*(Top 14-50 见后续增量实现)*

## 状态
`已成立`
