# Antigravity AI CLI 用户体验阻塞 Top 50 审计 (Round 25)

普通极客下载了仓库，在命令行运行脚本时会遇到如下阻塞：

| 阻塞项 | Token 证据 | 阻塞痛点与建议 |
|---|---|---|
| 1. 没有 `--help` | `chara_dasha.py` | 运行直接抛缺参错，无提示。需改用 `argparse`。 |
| 2. 日期格式硬编码 | `varshaphala.py` | 不支持 `YYYY/MM/DD`，必须死记 Python datetime 格式。 |
| 3. 时区混淆 | `local_accuracy_report.py`| 对于不同时区的基准不清晰。 |
| 4. 无法指定经纬度别名 | 必须敲 float。 | 不支持 `--location "New York"`，必须敲 40.71, -74.00。 |
| 5. JSON 缩进难看 | `scripts/` 的多个输出。 | 没有默认为 2 格缩进，导致满屏糊掉。 |
| 6. 缺 Windows 批处理 | `README.md` 全是 Mac/Linux 指令。| 加两行 `.bat` 启动说明。 |
| 7. 端口写死 | `jyotish_api_server.py` | 端口被占时抛异常，应支持 `--port` 随机 fallback。 |
| 8. Python 依赖报错 | `pip install` | `requirements.txt` 没锁死版本，随时跑不起来。 |

**副手下一轮任务**：锁定一遍所有依赖项的具体安全版本并输出 `requirements-locked.txt`。
**Codex 可做任务**：把 `chara_dasha.py` 用 `argparse` 改写并加上完整的 `-h` 说明。
**Codex 可做任务 2**：在 API Server 启动时加上端口占用检测。
