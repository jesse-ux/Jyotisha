# Antigravity AI Ashtakoot 外部样本采集教程草案 (Round 22)

合婚测试不像星盘，必须两套数据（男/女）一起录入。

| 步骤 | 具体执行方案 |
|---|---|
| 1. 5 个样本怎么填 | 准备 5 对公众人物或合成用例的 Moon Longitude。 |
| 2. 外部来源优先级 | AstroSage 网页版 > JHora 桌面版 > VedAstro API。 |
| 3. VedAstro API 采样 | 若调用 API，需截取返回的 JSON 体或界面。 |
| 4. AstroSage 页面采样 | 登录 AstroSage 的 Match Making 页面，截图最后 36 分的柱状图或表格。 |
| 5. JHora 合婚页面采样 | 打开 `Compatibility` 面板，截图 Ashtakoot 的表格。 |
| 6. 截图命名 | 必须遵守规范，如 `external_ashtakoot_couple_01_astrosage_evidence.png`。 |
| 7. 目标字段填写 | 依次填入 `target.varna`, `target.tara` 等，以及 `total_score`。 |
| 8. Kuja status 取值 | 将 AstroSage 中的 `Manglik` 状态翻译成 `no_dosha` 或 `strong_dosha` 填入 JSON。 |
| 9. 隐私 | 如果是测试真人（非明星），抹去名字、地点、出生日，仅留经度或分数表。 |
| 10. Validator | 运行 Validator。如果加起来的分数和 Total 差超过 0.01，打回。 |
| 11. 0/5 到 1/5 | 只要成功跑通一个，总的 Valid Packets 就会加一。 |
| 12. 不调参边界 | Ashtakoot 因为是固定常量表，其实不需要机器学习调参，但它通过了这个门禁，就证明我们的代码写对了常量映射。 |

**落地建议**：该草案应该放在 `references/oracle/` 旁边供外包人员参考。
