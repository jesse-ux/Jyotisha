# Antigravity AI 全球同品类能力差距复核 (Round 3)

## 对标说明
按开源覆盖度/普通用户可用度/AI Native 承载度的临时分层，本项目定位为“AI 原生的印度占星引擎”，但在传统静态计算能力堆砌与商业化包装上仍有可度量的差距。

## 差距复核对比

| 功能项 | 对标产品表现 | 当前项目表现 | 差距等级 P0/P1/P2 | 建议落点文件或接口 |
|---|---|---|---|---|
| **底层核心计算广度** | **VedAstro.Python**: 宣传拥有 `596+` 注册方法，包含各种极端细分的 Panchanga、匹配合婚和复杂天文方法。 | **当前项目**: `68` 个核心注册技法，主干链路已打通，主要集中在 D1/D9、Dasha、Shadbala、Ashtakavarga 等高频模块。 | P1 (功能广度落后) | `scripts/technique_registry.json`，逐步添加新计算方法 |
| **外部绝对值校准深度** | **PyJHora**: 完整复刻 JHora 的 Dasha 和 Shadbala 计算细则，通过长期打磨实现了无缝对齐。 | **当前项目**: D1/D9 黄经已对齐，但 Shadbala/Dasha 仍处于绝对值扩充期，缺少足够的外部 Oracle 基准靶心。 | P0 (置信度瓶颈) | `references/oracle/dasha_shadbala_oracle_cases.json` |
| **C端商业化产品完整度** | **AstroSage**: 拥有完整的 App 生态（排盘、合婚、Talk-to-Astrologer、多语言切换）。 | **当前项目**: PWA/浏览器前端已成型，支持本地 API 连通，具备 AI Chat 面板，但产品偏向“硬核开发者”和“演示面板”风格。 | P2 (商业化体验落后) | `jyotish-app/index.html`，丰富页面生态与交互引导 |
| **Web 报表表现力** | **Prokerala**: 在线排盘 UI 丰富，提供南北印度图表切换及各分盘的结构化可视化图表。 | **当前项目**: 仅有北印度图样式，且图表可视化渲染相对单一，强依赖文本面板（AI Prompt Pack 输出）。 | P2 (可视化能力单一) | `jyotish-app/main.js`，增加南印度图和 D-chart 可视化渲染 |
| **AI 原生架构 (优势)** | 其他平台大多仍为传统规则树匹配或简单的 RAG 问答封装。 | **当前项目**: 提供首创的 `ai_prompt_pack` 架构，将星盘参数与引擎断语作为 evidence_snapshot 直接注入 AI Context，极大减少幻觉。 | N/A (领先) | `jyotish-app/ai-chat.js`, `scripts/jyotish_api_server.py` |
