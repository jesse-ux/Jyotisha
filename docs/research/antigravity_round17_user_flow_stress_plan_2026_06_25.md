# Antigravity AI 用户端黑盒流程压力测试计划 (Round 17)

为了保证 Web 交付质量，列出 12 项必做测试：

| 流程 | 用户动作 | 预期结果 | 失败风险 | 建议自动化入口 |
|---|---|---|---|---|
| **静态 demo 无 API 首次打开** | 断开 API，打开 `index.html` | 显示“Local API required”横幅，屏蔽高级按钮 | 用户不知道服务已挂掉。 | `test_trust_center_exposes_oracle_evidence_intake_cards` |
| **本地 API 在线完整排盘** | 输入表单，点击计算 | 展现 D1、D9 盘和 Dasha 树 | API 超时或解析器挂掉。 | `test_cli_smoke.py` / Playwright |
| **Raman/KP ayanamsa 切换** | 在设置中更改 Ayanamsa | 重新请求排盘，度数偏移 | 缓存未更新，度数依然是 Lahiri。 | `test_frontend_productization.py` 补充 Ayanamsa 设置 |
| **AI Prompt Pack 复制** | 点击复制黑箱按钮 | 剪贴板获取 JSON 和 System Prompt | 内容为空或 JSON 破损。 | 按钮点击劫持事件拦截 |
| **Evidence Packet 下载** | 在 Intake 面板点下载 | 获得一份预填好的 draft JSON | 面板根本没渲染出下载按钮（如当前）。 | API 返回假数据包时模拟点击 |
| **Evidence Packet 导入失败** | 上传一个没有 `sthana` 的包 | 立即红灯，报错缺失字段 | Validator 防线失守（如当前）。 | 增加前端桥接 `validateOracleEvidence` 的 mock 测试 |
| **Evidence Packet 导入成功模拟** | 上传一个填满数据的包 | 变成绿灯状态，允许打包 | 解析不当。 | `test_api_server_security.py` |
| **移动端 Trust Center** | 手机宽度访问 Trust Center | 保持单列排版，内容不溢出 | CSS 崩坏，字体极小无法阅读。 | CSS `@media` grid columns 覆盖 |
| **PDF/HTML 导出** | 点击报告生成 | 弹出新窗口或文件包含 `ready_for_calibration: 0` | 导出接口崩掉，报告内未带 Calibration 声明。 | `test_api_server_security.py` 的 export 节点 |
| **保存/打开本地星盘库** | 点击 Save Chart 后重刷页面 | LocalStorage 保留上次出生参数 | IndexedDB 或 LocalStorage 被清空或格式错乱。 | Puppeteer |
| **Skill Workbench API Explorer** | 尝试发 curl 到 `/api/compute_dasha` | 正确返回大运 | 路由未开放。 | 接口监控 |
| **Oracle progress dashboard** | 页面初始化 | 展示 `0/5 Valid Packets` 等进度 | UI 缺失，无法吸引贡献（如当前）。 | UI 单元组件测试 |
