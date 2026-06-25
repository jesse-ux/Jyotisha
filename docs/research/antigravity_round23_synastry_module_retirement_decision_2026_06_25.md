# Antigravity AI synastry.py 去留决策 (Round 23)

随着 `ashtakoot.py` 的全面接管，我们需要审视旧文件 `scripts/synastry.py` 的去留：

| 检查项 | 结论 |
|---|---|
| 1. 哪些 import 仍在使用 | 🔴 `jyotish_api_server.py` 里已经不用了，但可能某些偏僻测试还在用。 |
| 2. 哪些测试依赖 | 发现 `tests/test_synastry.py`（若存在）可能还在跑旧入口。 |
| 3. 兼容价值 | 🔴 几乎为 0。里面全是只支持极粗略计算的残次品。 |
| 4. wrapper 改写？ | 🔴 不推荐。这会引入两层不必要的函数栈。 |
| 5. 删除风险 | 🟡 如果某些非核心 CLI 还在调用会报错。需要全量 `rg synastry` 确认。 |
| 6. 保留风险 | 🔴 极高。团队里新来的成员容易错误地调用旧 `synastry.py` 导致 36分结果分叉。 |
| 7. 最小重构建议 | 把 `scripts/synastry.py` 直接加上 `# DEPRECATED: Use ashtakoot.py instead` 并在里面抛个 Warning，先别删。 |
| 8. 测试建议 | 把所有还在调用 `synastry.py` 的用例换成 `ashtakoot.py`。 |
| 9. API 影响 | 无。API 已经切走。 |
| 10. 前端影响 | 无。前端只认 API 返回格式。 |
| 11. 文档影响 | 如果 README 里有写，需要改掉。 |
| 12. Round 24 建议 | 加入到下一轮清理计划中：全量抹除 `synastry.py` 物理文件。 |

**最小 Codex 改动建议**：不要在这个当口删文件，Round 24 再删，先专心填满 36分字典再说。
