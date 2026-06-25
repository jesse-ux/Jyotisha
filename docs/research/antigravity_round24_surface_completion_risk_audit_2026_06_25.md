# Antigravity AI 表面完成度风险清单 (Round 24)

| 风险项 | 表面状态 | 真实状态 | 判定 |
|---|---|---|---|
| 1. Ashtakavarga | 注册表完成 | 有 337 分总和校验，但缺乏各宫 UI 可视化 | 🟡 部分成立 |
| 2. Jaimini Chara Dasha | 注册表完成 | CLI 有，但前端无图表 | 🟡 部分成立 |
| 3. Panchang | 文档有规划 | 缺 API 缺 UI | 🔴 未成立 |
| 4. Muhurta | 文档有规划 | 缺 API 缺 UI | 🔴 未成立 |
| 5. Synastry | API/UI 连通 | 底层缺 VedAstro 字典常量 | 🟡 部分成立 |
| 6. Shadbala | API/UI 连通 | 内部能算出数字，但缺外部验证包，未做 production 调参 | 🟡 部分成立 |
| 7. Vimshottari Dasha | API/UI 连通 | 未证明起始时间、容差，未有外部截图 | 🟡 部分成立 |
| 8. BPHS 分盘计算 | 18/18 不变量通过 | 本地算得对，但解盘可信度存疑 | 🟡 部分成立 |
| 9. KP Horary | 无 | 彻底空白 | 🔴 未成立 |
| 10. AI Prompt Pack | 有弹窗 | 缺乏中文特定解盘提示，大模型会自由发挥 | 🟡 部分成立 |
| 11. PDF 导出 | 有下载 | 仅存原始 JSON 格式 | 🔴 未成立 |
| 12. 静态 Demo (PWA) | 可访问 | 本地算命只能调用写死数据 | 🟡 部分成立 |
| 13. Trust Center | UI 可见 | 完全依赖 0/5，还卡在人工录入环节 | 🟡 部分成立 |
| 14. 错误处理 | 偶尔能拦截 | Dasha 无效时间、越界经度等只在特定接口拦了 | 🟡 部分成立 |
| 15. 移动端拥挤 | 基本适配 | Dasha 表格在某些超窄屏溢出 | 🟡 部分成立 |
| 16. Yoga 识别 | 有 F1 指标 | 局限于内部 baseline 互测 | 🟡 部分成立 |

**副手下一轮任务**：梳理 Jaimini Chara Dasha 的 E2E 接口缺口。
**Codex 可做任务**：把 Ashtakavarga 的分宫矩阵绘制到前端 D1 盘下方。
