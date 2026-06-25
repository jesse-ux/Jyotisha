# Antigravity AI 前端合盘兼容字段复核 (Round 23)

由于后端新旧引擎切换，必须验证前端的 JSON 解析鲁棒性：

| 检查项 | 状态 | 结论 |
|---|---|---|
| 1. `is_match_approved` | 🟢 新引擎包含 | 前端目前还是读取 `is_approved`。 |
| 2. `is_approved` | 🟢 API 已补齐 | API 做了字典赋值透传。 |
| 3. `male_details` 等 | 🟢 新引擎包含 | 前端尚未去读取，而是继续读取旧名称。 |
| 4. `male` / `female` | 🟢 API 已补齐 | 安全着陆。 |
| 5. `assessment` | 🔴 新引擎未包含 | 这部分在新引擎中散落在了各 Kuta 的 description 中。 |
| 6. `additional_kutas` | 🟢 新引擎支持 | |
| 7. `BadConstellations` | 🔴 被替换 | 现名为 `mangal_dosha_status` 等。 |
| 8. `kuja_dosha_*` | 🟡 待完善 | 目前 API 还不输出，需要等字典写完一并加入。 |
| 9. 导出关系报告 | 🟡 未测试 | |
| 10. 保存关系案例 | 🟡 仅前端 LocalStorage | 因为不保存敏感信息，所以没事。 |
| 11. 移动端显示 | 🟢 正常 | `Ashtakoot` 独立表格设计得极好，不会溢出。 |
| 12. E2E 缺口 | 🔴 极高 | 我们没有自动测试测过前端到底是取 `is_approved` 还是 `is_match_approved`，目前全靠 API 人肉补丁撑着。 |

**最小 Codex 改动建议**：未来应让前端 Vue 组件改读新的 `is_match_approved` 和 `male_details` 字段。
