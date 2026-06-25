# Antigravity AI 用户黑盒流程压力测试计划 (Round 18)

| 场景编号 | 流程与用户动作 | 预期结果 | 失败风险 | 建议自动化 |
|---|---|---|---|---|
| 1 | 断开 API，首次打开静态 Web | 显示 Local API required | 用户卡在白屏 | Puppeteer/Playwright |
| 2 | 正常填表首次计算 | 显示基础盘与 Dasha | 引擎内部崩坏 | Pytest smoke |
| 3 | 切换 Raman Ayanamsa | 重新计算，数值微调 | 缓存不更新 | Playwright 元素内容比对 |
| 4 | 查阅 D1/D9/SAV | 信息准确展示 | UI 数据错位 | API 断言 |
| 5 | 打开 Dasha 边界说明 | 弹出弹窗解释外部校准 | 弹窗未绑定事件 | UI Test |
| 6 | 下载 Evidence Packet | 获取 draft 状态 JSON | 结构缺失 `target` | API JSON schema 校验 |
| 7 | 导入空 packet | 报错：缺失必填元数据 | 错误吞没 | Validator 黑盒模拟 |
| 8 | 导入本地引擎伪造的包 | 拦截提示非 external_verified | 防火墙击穿 | Validator 安全用例 |
| 9 | 导入缺 `kala` 分量的包 | 拦截提示 `missing_shadbala_component` | 放过残缺数据 | Validator mock 数据 |
| 10 | 导入完美七曜六分量包 | 绿灯，准备晋级 | json 解析错 | e2e test |
| 11 | 手机竖屏看 Trust Center | 表格不溢出，横向滚动或单列 | 布局挤碎 | @media css test |
| 12 | 导出综合 HTML 报告 | 包含 D1, D9, Dasha 和免责声明 | 报错 500 | `test_api_server_security.py` |
| 13 | 点击复制 AI Prompt Pack | 剪贴板带有系统提示词及 JSON | 剪贴板接口受限 | JS clipboard Mock |
| 14 | 查阅内置专业术语词典 | 抽屉正常弹出 | 数据加载阻塞 | UI Test |
| 15 | 两人合盘测试 | 正常出分（如 24/36） | Ashtakoot 未写完崩溃 | 引擎合盘测试 |
| 16 | 查看 Muhurta 吉凶时 | 标红 Rahu Kala 等 | Panchanga 算法崩 | 天文库测试 |
| 17 | KP Horary 选数字卜卦 | 正确推导时辰 | 时差算错 | KP 单元测试 |
| 18 | 输入极地纬度出生 | 提示可能不准或切换制式 | 系统完全抛异常 | 边界坐标测试 |
| 19 | 离线缓存计算 | PWA 提示无网但可用缓存 | 断网白屏 | Service Worker Test |
| 20 | API 挂掉后重试 | 友好提示重连 | 陷入死循环 | Error Boundary Test |
