# Antigravity AI Trust Center 真实进度仪表盘黑盒复核 (Round 17)

通过前端代码和组件搜索（`rg "Oracle Evidence Intake"` 等），目前进度仪表盘的展示依然缺失：

| 指标 | 是否可见 | 当前值 | 用户是否能理解 |
|---|---|---|---|
| **total template cases** | 🔴 否 | (后台为 5) | **未成立**。完全不可见。 |
| **valid packets** | 🔴 否 | (后台为 0) | **未成立**。完全不可见。 |
| **ready for calibration** | 🔴 否 | (后台为 0) | **未成立**。完全不可见。 |
| **production tuning allowed** | 🔴 否 | (后台为 false) | **未成立**。完全不可见。 |
| **D1/D9/SAV confidence** | 🔴 否 | N/A | **未成立**。完全不可见。 |
| **Dasha boundary calibration** | 🔴 否 | (后台 0/3) | **未成立**。完全不可见。 |
| **Shadbala absolute calibration**| 🔴 否 | (后台 0/4) | **未成立**。完全不可见。 |

**检查点**：
1. 运行 `npm run build --prefix jyotish-app`：构建成功，但界面中缺乏进度可视化组件。
2. 搜索 `jyotish-app/main.js`：仅能搜到 `Oracle Evidence Intake` 的基本标题，并没有针对 `total_packets` 和 `valid_packets` 的进度条。
3. 测试文件 `tests/test_frontend_productization.py` 报错缺失组件断言。

**修复建议**：Codex 需要在 `jyotish-app/main.js` 里的 `renderOracleEvidenceIntakePanel` 方法中，接收来自 API 返回的 `summary` 对象，将其包装为类似 GitHub 进度条或卡片的 DOM 节点挂载。

*(此测试无须人工截图介入)*
