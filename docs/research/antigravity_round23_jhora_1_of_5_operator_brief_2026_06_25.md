# Antigravity AI JHora 1/5 人工操作简明包 (Round 23)

操作员请注意，必须严格按照以下步骤：

1. 找一台 Windows 电脑，下载安装 [JHora 8.0 免费版](https://www.vedicastrologer.org/jh/).
2. 输入资料：`Steve Jobs` / `1955-02-24 19:15` / `San Francisco, CA` (122w25, 37n46)。
3. 在 Preferences 中，Ayanamsa 选 `Chitra Paksha (Lahiri)`，Nodes 选 `True Node`。
4. 截图 1：Dasha 选项卡第一行（Vimshottari Dasha 起点）。
5. 截图 2：Strength 选项卡中，Sun 到 Saturn 七大行星的 Shadbala 分项与总分。
6. 打码：用画图把这两人私密信息抹掉（此例为名人可不打码，但习惯要养好）。
7. 保存图片至 `references/oracle/artifacts/` 目录中。
8. 打开 `references/oracle/dasha_shadbala_oracle_cases.json`。
9. 找到 `"case_id": "template_steve_jobs_dasha_lahiri"` 的大括号块。
10. 将 `"status": "draft"` 更改为 `"status": "external_verified"`。
11. 填入截图里的数字：`vimshottari_start_date` 以及 `shadbala_components`。
12. 运行验收：`python3 scripts/oracle_evidence_validator.py`。
13. 若终端最后报 `valid_packets: 1` 即为大功告成！否则根据报错修补错填数字。
