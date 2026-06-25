# Antigravity AI 遗漏回归测试清单 (Round 21)

检查 25 项可能遗漏的系统链路：

| 功能环节 | 状态与决策 |
|---|---|
| 1. D1 盘计算 | 已有 |
| 2. D9 婚姻盘计算 | 已有 |
| 3. JHora Dasha 对标 | 需要外部 oracle |
| 4. JHora Shadbala 对标 | 需要外部 oracle |
| 5. Shadbala 负数拦截 | 已有 |
| 6. Ashtakoot 入口 UI | 已有 |
| 7. Ashtakoot 计分表 | **缺失** (P1) |
| 8. Kuja Dosha (火星煞) | 已有 |
| 9. 合婚时 Kuja 叠加豁免 | **缺失** (需用户决策/进一步研究) |
| 10. `runtime-smoke` 忽略 | 已有 |
| 11. Git 研究报告提交 | **缺失** (P0) |
| 12. D10 事业盘 | 已有 |
| 13. AI Prompt Dasha 进度 | 已有 |
| 14. AI Prompt Ashtakoot 进度 | **缺失** (P1) |
| 15. PDF 导出附带合婚 | **缺失** (待UI完成后做) |
| 16. Validator Ashtakoot | **缺失** (P1) |
| 17. API `/api/synastry` 测试 | 部分已有 |
| 18. JHora 指南中文化 | 已有 |
| 19. Trust Center 0/5 UI | 已有 |
| 20. Swiss Ephemeris 调用 | 已有 |
| 21. PyJHora 代码复制 | **不应做** (AGPL污染) |
| 22. AstroSage 代码复制 | **不应做** (商业维权) |
| 23. VedAstro (MIT) 复制 | 需要用户决策 (推荐) |
| 24. Ayanamsa (Lahiri) 对齐 | 需要外部 oracle |
| 25. True Node/Mean Node 对齐 | 需要外部 oracle |
