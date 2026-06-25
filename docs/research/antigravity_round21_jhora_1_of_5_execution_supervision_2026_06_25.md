# Antigravity AI JHora 1/5 采集最终监督执行清单 (Round 21)

既然前面这么多轮人类都没有按指示操作，本轮我们给出**最严酷**的 15 步拆解，任何一步不对立刻重来：

1. **环境**：不要在 Mac 上用 Python 模拟！找一台 Windows。
2. **JHora 截图 1**：必须截出 Preferences 里的 Ayanamsa 面板，证明选的是 Lahiri。
3. **输入**：Steve Jobs (1955-02-24, 19:15, San Francisco, CA)。
4. **Lahiri 设置**：Ayanamsa 必须是 `Chitra Paksha (Lahiri)`。
5. **Node 设置**：必须是 `True Node`。
6. **Vimshottari 截图**：截出 Dasha 起始时间，第一行。
7. **Shadbala 截图**：截出 Strength 面板里 `Sun` 到 `Saturn` 的 `sthana` 到 `total` 的完整 6x7 矩阵。
8. **文件命名**：必须叫 `external_template_steve_jobs_dasha_lahiri_evidence.png`。
9. **打码验收**：截图上如果有“我的电脑”、“微信”边框，直接判定无效。
10. **JSON 填写**：把刚才那个巨型矩阵里的数字，一个个敲进 `references/oracle/dasha_shadbala_oracle_cases.json` 对应的占位符。注意是**Rupa**，不要写上百的 Virupa。
11. **状态修改**：把 `status: draft` 改为 `"status": "external_verified"`。
12. **跑验证器**：`python3 scripts/oracle_evidence_validator.py`。
13. **`valid_packets: 1` 判据**：如果终端还报 `placeholder_unfilled`，打回去重新填。直到输出 `valid_packets: 1`。
14. **`ready_for_calibration: 1` 判据**：没这回事！1 个包不足以启动校准，必须 5 个全绿才会变成 1。现在系统依然锁死调参！
15. **重采情形**：只要填了负数，哪怕是 -0.01，也会被 Validator 红牌罚下。
