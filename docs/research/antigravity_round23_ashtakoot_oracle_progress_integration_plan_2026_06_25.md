# Antigravity AI Ashtakoot Oracle Progress 接入计划 (Round 23)

为使合盘功能尽早打破“闭门造车”，全面接入多 Oracle 体系：

1. **CLI 设计**：在执行 `python3 scripts/jyotish_engine.py` 时，返回的 `oracle_progresses` 数组将从长度 1 变为长度 2（追加 ashtakoot）。
2. **API 字段**：`/api/chart` 里的顶层字典必须增加 `oracle_progresses` 节点，并在其中包含 `scope: 'ashtakoot'`。
3. **前端 Fallback**：如果没有 API 连通，前端 JS 自己抛出的假结果也应带有这 2 个 scope 的空进度，以便触发免责红色 UI。
4. **Trust Center**：新建一个 `<OracleEvidenceCard scope="ashtakoot">` 组件挂载。
5. **AI Prompt Pack**：AI 将看到：“Ashtakoot 当前验证进度：0/5。警告：请不要给出绝对的合婚建议”。
6. **测试用例**：`tests/test_cli_smoke.py` 要查 `assert len(result['oracle_progresses']) >= 2`。
7. **文案**：UI 和 AI 中使用的中文名：“36分合婚匹配引擎进度”。

**最小改动路径**：在 `scripts/jyotish_engine.py` 的 `_oracle_progress_snapshot()` 里，强制查两次 Queue 解析器。
