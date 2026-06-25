# Antigravity AI CLI Table Mode 体验规格 (Round 27)

命令行工具 `scripts/jyotish_engine.py` 不能永远只吐一堆乱码 JSON 给程序员：

| 体验升级项 | 规格说明与方案 |
|---|---|
| 1. `--table` 参数 | 拦截结果字典，使用 `tabulate` 库打印漂亮的 ASCII 表格。 |
| 2. 星体表格 (Grahas) | 列名：Planet | Sign | Degree | House | Nakshatra | Pada | Rupa (Shadbala)。 |
| 3. 宫位表格 (Bhavas) | 列名：House | Sign | Degree | Occupants | Lord。 |
| 4. 运势表格 (Dasha) | 只打印当前和未来的前 3 个 Mahadasha 和 Antardasha，别刷屏 120 年。 |
| 5. 合婚模式 (`ashtakoot.py`) | 提供一个包装脚本，输入双人生日，输出 8 Kuta 的分数表格，底部打印总分。 |
| 6. 日历模式 (`muhurta.py`) | 输入月份，输出本月每天是不是吉日，带有 `[OK]` 或 `[RAHU]` 等标记。 |
| 7. JSON 缩进 | 如果用户不带 `--table`，强制 `print(json.dumps(res, indent=2))`。 |
| 8. 错误抛出 | 捕获所有 Exception，用红色的 `sys.stderr.write` 打印人话，隐藏 Traceback。 |
| 9. Codex 任务 1 | 🟢 Codex可做 | 在 `jyotish_engine.py` 加上 `import json` 并在结尾处改写 print。 |
| 10. Codex 任务 2 | 🟢 Codex可做 | 为 `ashtakoot.py` 加一个 `if __name__ == '__main__':` 接收双参数打印结果。 |
| 11. Codex 任务 3 | 🟢 Codex可做 | 为 `chara_dasha.py` 和 `varshaphala.py` 套上 `argparse`。 |
| 12. 副手下轮 1 | 🟢 副手可做 | 将所有的第三方 CLI 包依赖（如 `tabulate`, `colorama`）写进 `requirements.txt`。 |
| 13. 副手下轮 2 | 🟢 副手可做 | 调研如何让 Python CLI 输出带有 Emoji (如 🔴 🟢)。 |
| 14. 人工 | 🔴 否 | |
| 15. Github 吸引力 | 没有好用的 CLI，Geek 是不会给你点 Star 的。 |
| 16. 测试性 | TDD 非常容易，重定向 stdout 验证即可。 |
| 17. 性能 | 不影响 API 服务。 |
| 18. 分支 | 只在 `__main__` 块里做文章。 |
| 19. Python 版本 | 兼容 3.7+。 |
| 20. 总结 | 这是开源传播的第一门面。 |
