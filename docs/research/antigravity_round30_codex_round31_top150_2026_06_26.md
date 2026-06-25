# Antigravity AI Codex Round 31 Top 150 执行清单 (Round 30)

## Codex，别管数学了，改路由和前端！(Top 15)

1. 把这批 R30 的文件归档。
2. 写个 `scripts/sync_to_workbuddy.sh` 并执行，把 `SKILL.md` 推回云端位置。
3. 打开 `jyotish_api_server.py`，加一个 `@app.route("/api/tajika", methods=["POST"])`。
4. 打开 `jyotish_api_server.py`，加一个 `/api/dasha_list`。
5. 去 `main.js`，找到渲染 SVG 的地方，上面加一个 `<select id="vargaSelect">`，填入 D1-D60。
6. 修改 `ashtakoot.py` 里的假数据，去 MIT 库里把那 8 个真实的查分矩阵抄进来。
7. 把 `jyotish_engine.py` 的火星煞判断，从返回 `true` 改成返回 `Enum(HIGH_DOSHA, CANCELLED)`。
8. 给 `jyotish_engine.py` 增加命令行参数 `--table`，用 `tabulate` 打印结果。
9. 修改 `oracle_evidence_validator.py`，加断言：如果 Rupa 力量 > 20，必定报错（常识卡点）。
10. 用 `html2pdf.js` 给前端加上“生成运势 PDF”的下载按钮。
11. 去 `varshaphala.py` 检查它是不是依赖了外部毒库，如果是，用纯 `swisseph` 替换。
12. 前端给 Rahu Kala 时间段加上醒目的红色告警 CSS。
13. 修改所有的 500 html 堆栈异常，包裹一层 `try...except` 吐标准 JSON。
14. 添加全局 Ayanamsa 切换变量（默认 Lahiri），允许透传 Raman。
15. 制作一个离线断网警告弹窗（通过 js 监听 `navigator.onLine`）。

*(此 15 条足以消化掉大模型本轮的心智，剩余 135 条顺延排期。)*

## 状态
`已成立`
