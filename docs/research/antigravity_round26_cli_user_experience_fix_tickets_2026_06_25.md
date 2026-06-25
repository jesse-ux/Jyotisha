# Antigravity AI CLI 极客体验修复票据 (Round 26)

普通程序员 git clone 后，命令行体验的痛点必须消除：

| 体验票据 | 具体表现与修复方案 |
|---|---|
| 1. `chara_dasha.py` 裸奔 | 运行 `python3 scripts/chara_dasha.py` 不加参数，会抛难看的错。需用 `argparse` 接管，给出 `-h`。 |
| 2. `varshaphala.py` 门槛 | 参数硬编码，没法玩。改用 `argparse` 支持 `--year` 和 `--dob`。 |
| 3. `ashtakoot.py` 输入法 | 必须手敲月亮经度，非专业人士根本不知道月亮在哪。写个包装，让人可以输入男女生日，内部自己算度数。 |
| 4. Windows `.bat` 缺乏 | 很多极客用 Windows。写一个 `start_server.bat` 包装好 pip install 和 http server 启动。 |
| 5. CLI 输出糊脸 | JSON 没格式化。强制在所有的 CLI json output 处加上 `indent=2`。 |
| 6. 没有 requirements lock | 用 `pip freeze` 或 `pip-tools` 生成一把锁，免得未来库挂了。 |
| 7. 端口被占没提示 | API server 没起开，抛 Address already in use。应当捕获并友善提示。 |
| 8. 缺 CLI 排盘直出 | `jyotish_engine.py` 支持 `--mode text` 但依然杂乱，不如加个 `--table` 用 tabulate 库打印 ASCII 表。 |
| 9. Codex 任务 1 | 🟢 Codex可做 | 把 `scripts/chara_dasha.py` 改写，引入 `argparse`。 |
| 10. Codex 任务 2 | 🟢 Codex可做 | 去 `jyotish_api_server.py` 的启动处，套一个 `try/except OSError`。 |
| 11. Codex 任务 3 | 🟢 Codex可做 | 在 `ashtakoot.py` 加个友善的终端打印。 |
| 12. 副手下轮 1 | 🟢 副手继续做 | 去梳理一遍目前项目所需的全部第三方包，弄个清爽的 `requirements.txt` 出来。 |
| 13. 副手下轮 2 | 🟢 副手继续做 | 构想那个 ASCII Table 打印排盘的格式布局。 |
| 14. 需要人工 | 🔴 否 | |
| 15. 核心价值 | 第一印象决定极客会不会 fork 这个项目。 |
| 16. 测试 | 改完 argparse 后，确保原本调它的地方没崩。 |
| 17. 耗时 | 很小，纯粹是语法糖。 |
| 18. 重要性 | Github 传播利器。 |
| 19. 前置 | 无。 |
| 20. 总结 | 让每一个 Python 脚本都是一个好用的独立工具。 |
