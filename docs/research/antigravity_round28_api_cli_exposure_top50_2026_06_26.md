# Antigravity AI API/CLI 暴露冲刺 Top 50 (Round 28)

对开发者和极客用户极其重要的 CLI/API 改造：

## API 路由补充
1. 新增 `/api/tajika`：接收年份参数，吐出当年太阳返照盘。
2. 新增 `/api/dasha_list`：枚举当前盘支持的十几种 Dasha 及首尾时间。
3. 新增 `/api/export/ics`：让用户订阅接下来 30 天的吉凶日历。
4. 新增 `/api/search_yogas`：传入星体参数，反查古籍中哪些 Yoga 会匹配。
5. 修复所有 500 HTML 报错，包裹成标准的 `{ "error": "...", "code": 500 }`。

## CLI 体验进化
6. 为 `jyotish_engine.py` 添加 `--table`，用 `tabulate` 画出终端里的 ASCII 星盘。
7. 为 `jyotish_engine.py` 添加 `--format json --indent 2`。
8. 为 `muhurta.py` 添加入口：`python3 scripts/muhurta.py "2026-06" --lat 28 --lon 77` 打印出当月吉凶表。
9. 为 `ashtakoot.py` 添加入口：命令行一键比对两人生日，吐出 8 Kuta 打分。
10. 给所有的报错堆栈穿上 `try-except`，在终端打印友善红字。

*(Top 11-50 随模块解耦顺延)*

## 状态
`已成立`
