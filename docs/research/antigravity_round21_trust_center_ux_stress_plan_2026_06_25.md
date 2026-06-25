# Antigravity AI Trust Center 用户体验压力测试计划 (Round 21)

针对普通用户和贡献者访问 Trust Center 的极端体验制定压力测试：

| UX 关注点 | 预期反馈与防呆策略 |
|---|---|
| 1. 理解 0/5 | 必须加粗“当前处于外部校准召集期，系统尚未完成自我进化”。 |
| 2. 下载模板 | “下载”按钮必须指向带有详细占位符的 template json。 |
| 3. 打码警示 | 上传按钮上方加红框：**请务必使用马赛克涂抹您的真实姓名与位置！** |
| 4. 指南入口 | 显著放置 [JHora 截图采集向导] 的链接。 |
| 5. 误以为已校准 | 在 0/5 时，`production_tuning_allowed` 的红灯必须极具压迫感。 |
| 6. 移动端溢出 | 用 Playwright 模拟 320px 的小屏幕，确保 2 个进度条单列堆叠。 |
| 7. 上传失败解释 | Validator 的 400 报错必须中文化，例如“您的 Sun.sthana 缺少数据”。 |
| 8. 并行 Oracle 混淆 | UI 上必须分清：左边卡片是 Dasha/Shadbala，右边卡片是 Ashtakoot。 |
| 9. Prompt 阶段提示 | 确认复制的大模型前缀真的包含 `valid_packets: 0`。 |
| 10. 静态 demo 边界 | 若访问的是没有 API 后台的网页，应禁用上传功能，提示“纯静态版不开放数据治理”。 |
| 11. 贡献者 checklist | 增加一个前端确认框：“我已检查并清除了个人隐私”。 |
| 12. Playwright 覆盖 | 写一段测试用例自动验证 2 个卡片的加载与 0/5 的渲染。 |

**最小 Codex 改动建议**：给 `jyotish-app/main.js` 中的 Validator 返回加上错误解释。
