# Antigravity AI Round 19 给 Codex 的执行清单 (Round 18)

1. **当前已成立的能力**：
   - Shadbala 六分量的强拦截逻辑已在 `oracle_evidence_validator.py` 中写死。
   - `test_mobile_layout_keeps_dense_sections_single_column` 等前端门禁已修复并飘绿。
   - `.gitignore` 已成功阻挡 `output_report.txt` 等隐私文件。
   - `references/oracle/artifacts/README.md` 打码防泄漏红线文件已物理存在。

2. **当前未成立的能力**：
   - 前端 Web 的 Trust Center 依旧**没有画出任何真实的进度条 DOM**（例如 `valid_packets 0/5`）。

3. **必须先修的 P0/P1**：
   - **P1**: 在 `jyotish-app/main.js` 中把 `renderOracleEvidenceProgressDashboard()` 里的 HTML 正式绘制出来并插到面板顶端。

4. **可并行交给副手继续做的研究任务**：
   - Ashtakoot 36分合婚标准的学术黑盒对标（找一本古籍或者用 AstroSage）。

5. **需要用户人工外部截图的任务**：
   - 发放《第一条 JHora 样本公开教程草稿》，请求人为执行一次真正的 JHora 采集并 PR，打破 `valid_packets: 0` 的僵局。

6. **建议 Codex 立刻修改的文件**：
   - `jyotish-app/main.js`（渲染 dashboard）。
   - `.gitignore`（追加 `*.html` 测试报告垃圾）。

7. **建议新增/修改的测试**：
   - 在 `test_frontend_productization.py` 里加上 `assert "oracle-evidence-progress-bar" in main_js`。

8. **下一轮开源复用候选**：
   - `flatlib`（MIT）：参考星体面向对象的封装结构。

9. **下一轮 UI/UX 优化候选**：
   - Evidence 下载时在前端弹出 Confirm 对话框：“请确保您的截图文件已按 README.md 打码脱敏”。

10. **Top 20 ROI 排序任务 (前 5 节选)**：
   1. 画出 Trust Center 的 0/5 真实进度条 (UI)。
   2. 追加 `.gitignore` 过滤 html。
   3. 下载包弹出打码警示对话框。
   4. **人肉完成第一份 JHora 包！**
   5. Ashtakoot 评级引擎对标。
