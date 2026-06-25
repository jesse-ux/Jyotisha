# Antigravity AI covered -> complete 晋级清单 (Round 28)

目前有 58 个技法在 registry 里是 `covered`，意味着后端能算，但缺乏测试/UI。把它们升格为 `complete` 的 Top 25 路径：

| 被掩埋的技法 | 晋级 Complete 的条件 |
|---|---|
| **1. Tajika (年运盘)** | API: 暴露 `/api/tajika`。UI: 增加年份选择下拉框。测试: 验 Muntha 落点。 |
| **2. Chara Dasha (Jaimini运)** | API: 合并输出。UI: Dasha 树状图增加 Vim/Chara 切换。 |
| **3. D7 - D60 (深分盘)** | UI: 增加全分盘的 SVG 选择器下拉列表。 |
| **4. Panchanga/Muhurta** | UI: 提供带有月相、吉时、凶时的月历前端组件。 |
| **5. KP Sublords** | UI: 在行星列表中额外增加 RL/NL/SL/SSL 这四列强弱关系表。 |
| **6. Prashna (卜卦)** | UI: 单独提供一个按钮：“以当前地点时间立刻起一卦”。 |
| **7. Kuja Dosha (火星煞)** | 算法: 将 bool 改为 `high_dosha` 等多级 Enum。 |
| **8. Ashtakoot (合婚)** | 数据: 剥离假常量，抄入 VedAstro 的真实 8 矩阵。 |
| **9. Ashtakavarga (八字分)** | UI: 画出十二宫 0-8 的散点柱状图。 |
| **10. Shadbala 详情** | UI: 不止展示总 Rupa，点击后展开 6 个子项雷达图。 |
| 11-25. 各类长尾 Yoga | 需要在 `yoga_rules.json` 中写出详细的判定树，并在 UI 高亮。 |

## Codex 实施策略
不要去开新坑，先把这 58 个 `covered` 里的精华压榨出来！给 API 加路由、给前端加按钮，是最廉价的升级方式。

## 状态
`已成立`
