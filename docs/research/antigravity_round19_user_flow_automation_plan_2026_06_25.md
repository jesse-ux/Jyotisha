# Antigravity AI 全链路用户压力自动化测试建议 (Round 19)

为根治目前 240+ 全绿但掩盖 UI Bug 的问题，推荐使用 Playwright 覆盖以下 15 条（精简版）核心链路：

| 自动化用例名称 | 预期行为 | 自动化工具建议 | 暴露的潜在风险 |
|---|---|---|---|
| 1. 断网启动 | 页面正常刷出 Local/Cache 内容 | Playwright offline mode | PWA 挂掉，白屏 |
| 2. 下载 Evidence 空包 | 点击下载，收到 `status: draft` JSON | Playwright download intercept | 下载的是空文件/抛异常 |
| 3. 导入空包 | Validator 红灯，弹出 missing | Pytest 调用 Validator | 错误吞没 |
| 4. 导入缺 Shadbala | Validator 红灯，提示 missing_planet | Pytest | 放行残缺结构 |
| 5. 导入本地造假包 | 提示 must_not_come_from_local | Pytest | 防火墙被击穿 |
| 6. 导入完整 draft 包 | JSON 读写成功，但拦截晋级 | Pytest | 未检查 artifacts |
| 7. Trust Center Dashboard | `renderOracleEvidenceProgressDashboard` 被真实渲染为 DOM | Playwright `.oracle-evidence-progress-bar` | **(此前发生过的)** 隐式失败 |
| 8. 复制 AI Prompt | 剪贴板拦截成功 | Playwright Clipboard mock | 无权限或文案被截断 |
| 9. 切换 Lahiri 至 Raman | API 响应重算，DOM 刷新 | Playwright | 缓存穿透，数值不改 |
| 10. API 服务宕机 | Web 界面友好提示，无死锁 | Playwright fetch abort | 页面无限 Loading |
| 11. 手机分辨率看表格 | Dasha 表格单列或横向滚动 | Playwright Viewport (375x812) | CSS Overflow |
| 12. 黑盒包无 artifact 晋级 | 拒绝 `external_verified` | Pytest | 无图无真相的假包通过 |
| 13. Shadbala 单位负数 | 抛错 | Pytest | 数据投毒 |
| 14. Dasha 异常时间格式 | 解析异常 | Pytest | 后端崩坏 |
| 15. 合婚 Asthakoot (预留) | 测算出 36 分标准值 | Pytest | 尚未实现 |

**落地建议**：Codex 应当优先补齐第 7 条，即确保 Trust Center 的 DOM 渲染真实受 Playwright / UI 级别断言的保护。
