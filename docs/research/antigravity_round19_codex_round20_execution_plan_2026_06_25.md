# Antigravity AI 给 Codex 的 Round 20 执行计划 (Round 19)

1. **当前已成立能力**：
   - Shadbala 强校验、artifacts 物理与规约阻挡、前端 progress DOM 调用、移动端测试全绿。
2. **当前未成立能力**：
   - 真人还没去填那个史蒂夫·乔布斯的 JHora 真实模板（依然是 0 / 5）。
   - `.gitignore` 漏掉了测试生成的 HTML。
3. **必须先修的 P0/P1**：
   - [ ] 修改 `.gitignore`，增加 `runtime-smoke-report-*.html`。
   - [ ] 将当前工作树下所有 Round 19 报告进行 `git add docs/research/`。
4. **可直接修改的文件**：
   - `.gitignore`
   - `scripts/oracle_evidence_validator.py`（加入类型和非负校验）
   - `scripts/jyotish_engine.py`（把 valid_packets 传入 Prompt Pack）
5. **可直接新增的测试**：
   - `test_ashtakoot_compatibility.py` (空白占位)
   - `tests/test_playwright_e2e_stub.py`
6. **必须等待人工工具的任务**：
   - 发送《1/5 真实样本人工执行单》，呼叫人类用 Windows 跑一次 JHora。
7. **可复用开源候选**：
   - `VedAstro (MIT)`，`flatlib (MIT)`。
8. **只能参考项目**：
   - `PyJHora`, `AstroSage`。
9. **隐私/许可证风险**：
   - 绝不可复制 AGPL 的 PyJHora 逻辑；务必保障 artifact 打码要求被遵守。
10. **Top 20 ROI 任务节选**：
    1. 修复 `.gitignore` 并 Git Commit 所有的文档（P0 卫生）。
    2. 呼叫真人填报 JHora Steve Jobs 样本（P0 业务）。
    3. Shadbala 类型校验拦截（P1 质量）。
    4. 把 valid_packets 装入 Prompt（P1 AI）。
    5. 启动 Ashtakoot 常数表搭建（P0 增长引流）。

> 下一步建议 Codex 优先：修改 `.gitignore` 阻断测试 html 垃圾上云，然后把本轮副手写的 14 份报告 `git add` 并提交，做一次代码库快照！之后立刻拉住真人去跑 JHora，把 `1/5` 拿下！如果等不到真人，可以先着手准备 Ashtakoot 36 分合婚的 JSON 常量表。
