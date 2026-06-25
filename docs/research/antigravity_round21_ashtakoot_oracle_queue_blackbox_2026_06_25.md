# Antigravity AI Ashtakoot Oracle Queue 黑盒复核 (Round 21)

| 检查项 | 结论 | 证据/说明 |
|---|---|---|
| 1. `case_id` 是否唯一 | 🟢 唯一 | `ashtakoot_public_couple_lahiri_01` 等彼此独立。 |
| 2. 隐私等级 | 🟢 已包含 | 含有 `public_figure` 和 `synthetic` 标签。 |
| 3. 是否非生产状态 | 🟢 已成立 | 所有包都是 `template_only`，需要外部抓图填充。 |
| 4. Target 字段 8 Kuta 覆盖 | 🟢 已成立 | 包括 `varna`, `vashya`, `tara`, `yoni`, `graha_maitri`, `gana`, `bhakoot`, `nadi`。 |
| 5. 包含 `total_score` | 🟢 已包含 | 目标字段明确要求填写合盘总分。 |
| 6. 包含 `kuja_status` | 🟢 已包含 | 火星煞对冲状态纳入标定。 |
| 7. 标明 36 分制 | 🟢 已说明 | 字段描述中要求必须用 `ashtakoot_36_point` 规则。 |
| 8. Artifact 命名要求 | 🟢 已包含 | 要求截图并存入 `references/oracle/artifacts/`。 |
| 9. Queue 识别类型 | 🟢 已成立 | `target_modules: ["ashtakoot"]`。 |
| 10. 是否误触发调参 | 🟢 安全阻断 | draft 包被 validator 全部挡住。 |
| 11. 泄露关系资料 | 🟢 无风险 | 目前全是模板或合成空包，未有真实用户数据。 |
| 12. Validator 支持 | 🟡 尚需开发 | 亟需为 8 个 Kuta 各自分配独立的 0-8 数值边界强校验。 |

**最小 Codex 改动建议**：在 `oracle_evidence_validator.py` 里为 `ashtakoot` 新增一套专门的 8 Kuta Range Check。
**命令复现**：`python3 -c "import json; print(json.load(open('references/oracle/ashtakoot_oracle_cases.json'))[0]['target_fields'])"`
