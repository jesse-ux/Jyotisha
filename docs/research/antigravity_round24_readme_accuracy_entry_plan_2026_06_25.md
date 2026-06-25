# Antigravity AI README 本地准确率透出计划 (Round 24)

为了让每个 clone 代码的人知道我们的占星引擎有多准：

| README 建议加入的内容块 | 意图与说明 |
|---|---|
| 1. 一条命令测准确率 | `python3 scripts/local_accuracy_report.py --format markdown` |
| 2. 标示可信计算 | 明确：**排盘、落座、分盘、不变量和 Yoga 分析** 均基于本地基线，属于**高置信度计算**。 |
| 3. 标示不代表精准 | 明确：**时序大运推断、七曜力量换算、合婚算法** 仍需要大量人工比对，不可盲信。 |
| 4. 如何提交外部 oracle | 请参阅 `docs/research/` 中关于如何用 JHora 截图并提 PR 给我们的指南。 |
| 5. 解读 0/5 | 说明 0/5 不是程序 bug，而是开源社区缺乏真实数据贡献的诚实体现。 |
| 6. 如何测试前端 | `npm run build && npm run preview` |
| 7. 质量门禁说明 | `python3 scripts/run_quality_gate.py` 是每个 contributor 必须过的。 |
| 8. 隐私协议 | 再次强调不上传任何经纬度和出生时间。 |
| 9. BPHS 不变量 | 列出我们捍卫的 18 条古典占星数理底线。 |
| 10. 许可证警告 | README 顶部加红字：严禁从本项目吸入带有 AGPL 污染的代码。 |
| 11. Asthakavarga 得分 | 写明总分必须是绝对的 337，不容差池。 |
| 12. Dasha 起点漂移 | 说明时区、历法和岁差对起步日期影响极大。 |
| 13. UI 状态 | 前端处于 Beta。 |
| 14. 引擎语言 | Python 3.10+。 |
| 15. AI 占卜免责 | 我们只是计算引擎，大模型说你会离婚，我们不背锅。 |
| 16. 落地位置 | 插在 Installation 和 Contributing 之间。 |

**副手下一轮任务**：写一份完美的 README 新版草案大纲。
**Codex 可做任务**：按照上述 16 点直接覆写 `README.md` 的 `Accuracy` 章节。
