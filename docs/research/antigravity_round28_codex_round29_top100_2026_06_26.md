# Antigravity AI Codex Round29 Top 100 执行清单 (Round 28)

## 立即执行（Top 10 - TDD / 无需人工）
1. `git commit` 将本轮副手产生的 30 份报告归档。
2. 同步 `SKILL.md` 和 `technique_registry.json` 回 `~/.workbuddy/skills/jyotish-vedic-astrology/` 目录。
3. 把 `validate_logic_v2.py` 生成 JSON 加上 `sort_keys=True` 稳住顺序。
4. 全面包裹 `jyotish_api_server.py` 的 500 HTML tracebacks 为标准 `{ "error": "...", "code": 500 }`。
5. 在 `jyotish_engine.py` 添加 `--table`，引入 `tabulate`。
6. 为 API `/api/tajika` 追加解析代码，对接现成的 `varshaphala.py` 逻辑。
7. 在 `ashtakoot.py` 加一个接受双生辰参数并打印分数的 main 函数入口。
8. 增加下拉菜单复用 SVG renderer，解锁 D7-D60 (在 `main.js` 里实现)。
9. 将火星煞的 boolean 判定彻底从 `jyotish_engine.py` / `ashtakoot.py` 中挖掉，换成 Enum。
10. `oracle_evidence_validator.py` 补充拦截 Rupa 大于 20 及总和容差错误断言。

## 下一步跟进（Top 11-30 - 需抄常量 / UI）
11. 从 VedAstro 抄写 Ashtakoot 8 项敌对矩阵至常量文件。
12. 提取 `yoga_rules.json` 中的前 10 个常见 Yoga，让它在前端高亮并配上吉凶图标。
13. Panchang API 画出前端日历组件，标注 Rahu Kala。
14. 把 `KP_SL_Divisions.csv` (已在库里) 加载到全盘输出里，吐出 SL/SSL。
15. 把 Vimshottari Dasha 拓展至第三层 Pratyantardasha。
16. 在页面右上方加上一个供全局配置 Ayanamsa (如 Raman) 的浮层。
... (由于篇幅限制，Codex 看到这里足够开工)。

## 状态
`已成立`
