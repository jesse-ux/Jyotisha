# Antigravity AI CLI Productization Top 30 (Round 30)

## 拯救黑框框体验

CLI 是占星程序员和测试脚本的直接交互层。

| 缺陷现状 | 目标改造 (CLI Top 30 精华) |
|---|---|
| `python3 scripts/jyotish_engine.py` 默认喷涌 JSON。 | **引入 `--table`**。用 `tabulate` 打印漂亮的 ASCII 表：<br>`\| Planet \| Sign \| Degree \| Status \|` |
| 无法直接测合婚。 | **新增 `scripts/ashtakoot.py` 入口**。接受两人 JSON 路径，终端打印 8 项分数。 |
| 错误信息抛出巨长的 Python Traceback。 | **拦截错误**。如果度数超限，红字打印 `[Error] Moon degree > 30` 然后 `sys.exit(1)`。 |
| 查当月黄历很难。 | **`scripts/muhurta.py` 入口**。跑 `--month 2026-06` 打印每天的吉凶日历。 |
| 看不到岁差。 | **强制在星盘头打印**：`Ayanamsa: Lahiri (24.1234°)`。 |
| `run_quality_gate.py` 的进度条太死板。 | 引入 `tqdm` 或者 `rich` 库，画出漂亮的单元测试进度条。 |

## 状态
`已成立`
