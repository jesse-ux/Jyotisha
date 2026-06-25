# Antigravity AI 商用 PDF 导出规格 (Round 28)

## 动机
占星师希望能在软件里点一下，直接生成给客户看的带几十页的长篇 PDF 报告，以收取咨询费。这是软件商业变现的关键。

## 包含元素
1. 第一页：品牌 Logo，客户名字，精美的主盘 D1 和 Navamsha D9 矢量图。
2. 第二页：行星经纬度和尊贵度表格，力量 Shadbala 柱状图。
3. 第三页：长达 120 年的 Vimshottari Dasha 时间表树状图缩略。
4. 第四页：AI 的解盘分析文本和 Yoga 的罗列（必须在最底下印上我们的“免责警告”和 Ayanamsa 信息）。

## 技术实现
不要在 Python 后端做 PDF！排版太痛苦。
直接在前端使用 `Puppeteer`（无头浏览器）或者轻量的 `html2pdf.js` 把 DOM 直接打印为 A4 样式 PDF。

## 状态
`未成立`
