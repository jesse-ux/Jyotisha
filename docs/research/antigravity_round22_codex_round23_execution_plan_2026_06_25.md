# Antigravity AI Codex Round 23 执行计划 (Round 22)

**已完成项纠偏**：Codex 已经做完了 `git commit` 以及 Ashtakoot 的边界（0-36, 0-8）控制！干得非常漂亮。

### Top 10 下一步

1. **[人工拦截]** 找个真人执行 Report L（跑 JHora 截两张图），这是生死线。
2. **[Git Push]** `git add docs/research/antigravity_round22*` 然后双重 `git push` 上云，保住今天的所有架构思考。
3. **[移植字典]** 去 Github 搜 `VedAstro/VedAstro` 里的 `MatchCalculator.cs`。
4. **[构造字典]** 把里面的 8 个打分逻辑硬写成 Python Dict 放进 `scripts/ashtakoot_constants.py`。
5. **[联通主线]** 把 `scripts/ashtakoot.py` 里的假 `0` 替换成调用 `ashtakoot_constants.py`。
6. **[Kuja 枚举]** 去 Validator 给 `target.kuja_status` 加上 Enum (no_dosha, 等) 的范围拦截。
7. **[Shadbala 总分]** 去 Validator 给 七曜加上 `sum ≈ total` 的容差以及超 `20` 拦截。
8. **[AI Prompt 进度]** 去 Engine 里追加 `ashtakoot_oracle_progress` 下发给大模型。
9. **[UI 改造]** 去前端把 Trust Center 的卡片拆成左右两张（大运、合婚），独立显示 0/5。
10. **[测试]** 跑 `pytest tests/test_ashtakoot.py`。

### 核心约束
- **不应复制**：PyJHora (AGPL)。
- **最小实现**：字典越平铺越好，别搞什么复杂类继承。
- **Commit 建议**：先 Push 现有的文档！然后再建新分支写字典代码。
