# Antigravity AI Ashtakoot 外部采集包短版 (Round 23)

请操作员在网上寻找真实的合盘打分对标依据：

1. **VedAstro (推荐)**：打开 `https://vedastro.org` 的 Match 页面。
2. **AstroSage**：或者打开 AstroSage 的 `Kundli Matching`。
3. **录入 JSON**：打开 `references/oracle/ashtakoot_oracle_cases.json`。
4. 将其中一个 draft 包的 `"status": "draft"` 更改为 `"status": "external_verified"`。
5. 照着网页上给出的 `varna`，`tara`，`yoni` 分数，填入 JSON 的对应字段。
6. 最后把加起来的 `total_score` (最大 36 分) 也填入。
7. 如果页面显示女方或男方有 `Manglik Dosha`，请在 `kuja_status` 里填入 `"strong_dosha"`。
8. 网页截图一张，抹掉人名，存入 `artifacts/` 目录。
9. 在 JSON 里的 `external_artifact` 字段填入该截图的文件名。
10. 运行验收：`python3 scripts/oracle_evidence_validator.py`。
11. 直至输出不再有报错信息为止！
