# Antigravity AI Ashtakoot 合婚突破方案 (Round 19)

| 破冰维度 | 当前状态与计划 |
|---|---|
| 1. 当前 Ashtakoot 能力 | 🔴 完全缺失。系统现在只能算两个人的单盘，缺乏 36 分合婚的交叉计算体系。 |
| 2. 前端是否露出 | 🔴 没有，在 `Relationship` 面板只有 D9 与 Dasha 同步，没有 Guna 36 分计算器。 |
| 3. API 是否已有 | 🔴 接口 `POST /api/compatibility` 还未建立 8 项（Varna, Vashya, Tara...）的数据模型。 |
| 4. 需要哪些 UI | 🟡 需要一个带两组输入框的表单（Boy & Girl），以及一个 8 行 4 列（得分、满分、名目、解读）的评级结果表格。 |
| 5. External Oracle 需求 | 🟡 需要新增 `dasha_shadbala_oracle_cases.json` 里的 3 个 Ashtakoot draft cases 才能保障其不偏离 JHora。 |
| 6. 可复用开源候选 | 🟢 **VedAstro (MIT)** 里面的 `Ashtakoot` 算法矩阵和常数表。 |
| 7. 不可复制项目 | 🛑 **PyJHora / AstroSage**。绝不可抄袭代码。 |
| 8. 测试建议 | 🟡 建立 `test_ashtakoot_compatibility.py`，用硬编码的 Nakshatra 落点组合对齐 36 分标准答案。 |
| 9. 首批 3 个样本建议 | 1. 完美 36分 组合（验证满分）。2. Nadi Dosha 严重冲克导致 0 分组合（验证拦截）。3. Bhakoot Dosha 被木星庇护豁免的组合（验证高级异常逻辑）。 |
| 10. Codex 最小实现顺序 | 1. 定义常数映射表。2. 写好 8 项打分引擎。3. 写 API Endpoint。4. 在前端 Trust Center 旁边画合婚面板。5. 添加 Oracle Case。 |

**落地建议**：一旦 1/5 样本破冰完成，Ashtakoot 合婚将是我们在流量获取与用户增长上的绝对 P0。建议下一轮立刻排期。
