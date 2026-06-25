# Antigravity AI 外部 Oracle 第一包破冰指令 V2 (Round 25)

给那位愿意花 30 分钟安装 JHora 的英雄：

| 操作步骤 (30 分钟极限流) | 具体指引 |
|---|---|
| 1. 软件准备 | 下载安装 `JHora 8.0`，无脑一直点 Next，免费。 |
| 2. 创建档案 | 点左上角 New，填 Steve Jobs，1955-02-24，20:15:00，时区 8:00 West（注意是 West！），San Francisco, CA。 |
| 3. 勾选选项 | 顶部菜单栏 `Preferences -> Related to calculations -> Ayanamsa`，确保是 Lahiri。 |
| 4. 截第一张图 | 界面下方有个叫 `Dasa` 的大 Tab，点开，会有个 `Vimsottari Dasa`。截图。里面有出生的第一个大运起运时间。 |
| 5. 截第二张图 | 界面下方有个叫 `Strengths` 的大 Tab，点开，会有一排带小数点的值，找以 `Rupas` 为单位的，截图。 |
| 6. 涂抹隐私 | 用 Windows 自带截图工具的笔，把左上角乔布斯的名字和出生经纬度划掉（为了演练素人隐私保护）。 |
| 7. 打开 JSON | 打开本项目里的 `references/oracle/dasha_shadbala_oracle_cases.json`。 |
| 8. 抄起运 | 找到 `steve_jobs`，把截图里的大运时间填进 `vimshottari_start_date`。 |
| 9. 抄七曜 | 往下，把截图里的日、月、火、水、木、金、土的 Rupa 值填进去。 |
| 10. 宣誓完工 | 把 `status` 改成 `external_verified`。 |
| 11. 验证 | 跑 `python3 scripts/oracle_evidence_validator.py`。出绿字，你就拯救了这帮 AI。 |
| 12. 为什么非要你做 | 因为连我都无法驱动一个 GUI 鼠标。 |
| 13. 下一步 Codex 1 | 🟢 Codex可做 | 把这个 V2 教程贴到项目的 README 里！ |
| 14. 下一步 副手 | 🟢 副手继续做 | 准备在 1/5 破冰后，开启 Shadbala Rupa 的自动调参机器学习脚本！ |
| 15. 需要人工 | 🟢 需人工 | 全文就是给人工写的。 |
