# Antigravity AI 第一条真实 Oracle 样本阻塞清单 (Round 24)

距离打破 0/5 魔咒，我们只差这临门一脚。到底卡在哪？

| 阻塞项 | 具体明细与应对 |
|---|---|
| 1. 需要谁操作 | **必须是拥有 Windows 系统的真人用户或外包人员。** |
| 2. 操作哪款工具 | 免费下载安装 `JHora 8.0`（Jagannatha Hora）。 |
| 3. 保存哪个截图 | `Steve Jobs` 1955星盘的 Dasha 第一页，以及 Strength (Shadbala) 矩阵表。 |
| 4. 填哪些字段 | 打开 `references/oracle/dasha_shadbala_oracle_cases.json`。 |
| 5. 改状态 | 将该块 `"status": "draft"` 改为 `"external_verified"`。 |
| 6. 改起运时间 | 将 JHora 里看到的出生大运起运日（如 `1955-02-24` 或之前）填入 `vimshottari_start_date`。 |
| 7. 改 Shadbala | 看着图，把七颗星的 Rupa 值（带小数的）全抄进 `shadbala_components` 里。 |
| 8. 改截图路径 | 把图片放入 `artifacts/`，并在 JSON 里填入文件名。 |
| 9. 命令如何验收 | `python3 scripts/oracle_evidence_validator.py`。 |
| 10. 隐私打码 | 必须用画图工具涂掉原图顶部的隐私资料，尽管乔布斯是公众人物，但习惯要养好。 |
| 11. 成功后改变什么 | 终端输出 `valid_packets: 1`，引擎不再锁死在 0%。 |
| 12. 为什么副手不做 | 我没有 Windows，且无权下载第三方闭源客户端并操纵 GUI 点击录入。 |
| 13. 为什么 Codex 不做 | 同上，它只懂敲代码。 |
| 14. 替代方案 | 只有人类才能走通这“第一桶数据”的破冰！ |
| 15. 是否阻碍开发 | 不阻碍写代码，但严重阻碍算法的合法性宣称。 |
| 16. 下一步 | 派单给任何一个非 AI 人类！ |

**副手下一轮任务**：继续写长篇大论催人。
**Codex 可做任务**：无能为力，只能等待。
