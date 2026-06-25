# Antigravity AI PyJHora/JHora 对标差距专报 (Round 24)

| 功能点 | 本项目现状 | JHora 状态 | 差距 | 实现优先级 |
|---|---|---|---|---|
| 1. D1 - D60 完整排盘 | 部分(15个) | 全包 | 缺极高阶分盘 | P3 |
| 2. Vimshottari Dasha | 有 | 有 | JHora 提供 5 层以上，我们只给 3 层 | P1 |
| 3. Yogini Dasha | API有 | 有 | 我们无前端图表 | P2 |
| 4. Shadbala Rupa | 有 | 有 | 缺绝对值对标 | P0 |
| 5. Ashtakavarga | 有 | 有 | 缺散点图 | P2 |
| 6. Tajika 年盘 | API有 | 有 | 我们缺 UI | P2 |
| 7. Chara Dasha | API有 | 有 | 我们缺 UI | P2 |
| 8. 恒星/岁差自由选 | 无 | 全包 | 我们仅支持 Lahiri | P1 |
| 9. 真/平交点选 | 无 | 全包 | 我们仅支持 True Node | P1 |
| 10. 自定义 Ayanamsa | 无 | 有 | | P3 |
| 11. Panchang (5要素) | 无 | 有 | 完全空白 | P0 |
| 12. Muhurta (择时) | 无 | 有 | 完全空白 | P0 |
| 13. KP System | 无 | 有 | 完全空白 | P1 |
| 14. Prashna | 无 | 有 | 完全空白 | P2 |
| 15. Yoga 分析器 | 有(千种) | 有(极多) | 我们的更易读，但规则数量暂不如它 | P2 |
| 16. 打印与 PDF 导出 | JSON仅 | 完美PDF | 我们还停留在极客模式 | P2 |

*(受限展示核心 16 项)*

**副手下一轮任务**：梳理 JHora 的 Panchang 的 5 要素计算公式。
**Codex 可做任务**：为 Vimshottari 增加用户可选择的 Ayanamsa 下拉框传参。
