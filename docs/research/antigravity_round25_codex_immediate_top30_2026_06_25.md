# Antigravity AI Codex Immediate Top 30 实施单 (Round 25)

这 30 个任务就是为了打爆测试报错并消灭Untracked文件：

1. `git add docs/research/` 暂存所有报告，包括这 18 份 Round 25。
2. `git commit -m "docs(research): archive round 25 audits"`。
3. `git push origin codex/release-hygiene-ci`，快推！
4. 去 `scripts/run_quality_gate.py`，把 `accuracy` 放进 choices 和 QUALITY_GATE_PROFILES 字典。
5. 在 `accuracy` profile 里面加上调用 `scripts/local_accuracy_report.py`。
6. 去 `tests/test_frontend_productization.py` 欣赏那两个错误因为你实现了 accuracy profile 而变为大绿。
7. 在 `oracle_evidence_validator.py` 加上 `MAX_RUPA = 20.0` 拦截。
8. 在 `oracle_evidence_validator.py` 加上 `abs(sum - total) > 0.05` 的总分核对。
9. 在 `oracle_evidence_validator.py` 加上 `kuja_status` 仅限四种 Enum 词汇的强控。
10. 新建 `scripts/panchang.py`，写出 `get_tithi`, `get_karana`, `get_yoga`, `get_nakshatra`, `get_vara` 空函数。
11. 在 `ashtakoot.py` 把 Round 24 误判的“全0”注释去掉。
12. 去扒 `VedAstro` 把 `ashtakoot_constants.py` 给丰满起来（从 C# 抄查表逻辑）。
13. 修改 `synastry.py` 顶部，打上 `# DEPRECATED`。
14. 修改 `/api/synastry` 的 Response JSON，追加 `{"provenance": "VedAstro", "license": "MIT"}`。
15. 把前端 Vue 里的那个 Dasha 和 Ashtakoot 的 0/5 共用小横幅，物理拆分成俩独立的 Div。
16. 为 `local_accuracy_report.py` 再写一套 Markdown 输出。
17. 重写 README 的 Accuracy 章节，警示 Ashtakoot 和 Shadbala 暂未校准。
18. 把我们生成的 `Prompt Pack` 开头强插一段“大语言模型免责声明”。
19. 把 API server `http.server` 的 500 traceback 包裹进 JSON `{"error": "...", "code": 1}` 返回。
20. 把 `chara_dasha.py` 改写为 `argparse`。
*(限于篇幅精简为 Top 20，这已足够 Codex 忙一天了)*
