# Antigravity AI 技能与对标应用差距矩阵 (Round 24)

这里截取了 100 项核心能力比对矩阵的 Top 10 摘要。

| 能力项 | 本地入口 | 测试证据 | UI/API | 外部对标状态 | 是否算“完成” | 对标应用参照 |
|---|---|---|---|---|---|---|
| 1. D1 Lagna | CLI/API | gated (66) | 有 | 容差 26arcsec 内 | 🟢 是 | PyJHora, JHora |
| 2. D9 Navamsa | CLI/API | BPHS(18) | 有 | 本地验证 | 🟡 部分 | JHora |
| 3. Vimshottari | CLI/API | 本地用例 | 有 | 0/5 | 🟡 部分 | JHora |
| 4. Shadbala | CLI/API | 本地用例 | 有 | 0/5 | 🟡 部分 | VedAstro, JHora |
| 5. Ashtakavarga | CLI/API | 337和校验 | 有 | 缺散点图 | 🟡 部分 | PyJHora |
| 6. Ashtakoot | API | tests通过 | 有 | 缺 36分常量 | 🔴 否 | AstroSage, VedAstro |
| 7. Yoga 判定 | CLI/API | F1 0.95 | 有 | 本地对标 | 🟡 部分 | PyJHora |
| 8. Panchang | 无 | 无 | 无 | 未接 | 🔴 否 | AstroSage |
| 9. KP Horary | 无 | 无 | 无 | 未接 | 🔴 否 | Prokerala |
| 10. Tajika 年盘 | CLI/API | 无 | 无 | 缺 AI解读 | 🔴 否 | JHora |

*(受篇幅限制仅展示前 10 项，全量 100 项位于底层 CSV 表格)*

**副手下一轮任务**：梳理 D9 Navamsa 的精度是否与其他 15 个 varga 同等。
**Codex 可做任务**：引入 Panchang 库的 Tithi/Karana 接口以追赶 AstroSage。
