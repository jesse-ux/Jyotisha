# Antigravity AI 错误 JSON 包装审计 (Round 27)

我们的 API 在抛错时必须像一个优雅的商业框架，而不是吐出一坨难看的 Python Traceback。

| 审计项 | 现状与问题描述 |
|---|---|
| 1. 全局 Exception 捕获 | 🟡 `jyotish_api_server.py` 在 `do_POST` 结尾有 `except Exception as e: self.send_error(500, str(e))`，这会导致前端收到 HTML 格式的 500 错误页。 |
| 2. JSON 包装要求 | 前端解析 `await response.json()` 时，如果碰到 HTML 就会报 `SyntaxError: Unexpected token < in JSON at position 0`。 |
| 3. 标准错误响应结构 | 必须统一下发：`{ "success": false, "error": "具体的错误信息", "error_code": "ERR_INTERNAL" }`。 |
| 4. AI Prompt 模块抛错 | 🟢 AI 在生成 prompt 失败时，似乎已被捕获为 `{ "success": false }`。 |
| 5. Oracle Evidence Validator | 🟡 跑 Python 脚本时直接 `sys.exit(1)` 并抛出 `ValueError`，这在 CLI 是没问题的，但如果被 API 包装调用，必须转成 JSON。 |
| 6. PDF 导出报错 | 🔴 如果后端缺少 PDF 库或者生成失败，会超时或者直接炸 HTTP 500。 |
| 7. 日历 / Muhurta | 🟡 参数如果缺了 `activity` 或者时间解析不对，可能会报 `KeyError` 导致 500 HTML。 |
| 8. 修复方案 1 | 重写 `BaseHTTPRequestHandler.send_error`，强制让它输出 `application/json` 而不是 `text/html`。 |
| 9. 修复方案 2 | 在 `do_POST` 和 `do_GET` 最外层包裹一个大的 `try...except`，然后 `self.send_response(500)` 配合 `json.dumps({"error": ...})`。 |
| 10. 测试用例验证 | 写一个必定报错的 API 请求（比如传一串乱码 JSON 给 `/api/chart`），断言返回体的 content-type 和字段。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 在 `jyotish_api_server.py` 的处理循环外围，加上 JSON 返回的异常拦截。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 去掉代码里所有的 `self.send_error(500, ...)`。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 新增 `test_api_server_security.py::test_api_returns_json_on_exception` 断言。 |
| 14. 副手下轮 1 | 🟢 副手可做 | 罗列各种业务异常（比如 `InvalidBirthDateError`），建议专门的 error_code。 |
| 15. 副手下轮 2 | 🟢 副手可做 | 审查前端 `main.js` 里的所有的 `fetch` 后的 `catch`，确保它们能优雅显示那个 error 字段。 |
| 16. 人工 | 🔴 否 | |
| 17. ROI | 高。极大降低联调排错成本。 |
| 18. 开发体验 | 让接口变得具备现代 REST API 的基本素养。 |
| 19. 代码洁癖 | 防止 Traceback 泄露服务器目录结构信息。 |
| 20. 总结 | 别再给前端喂 HTML 报错了。 |
