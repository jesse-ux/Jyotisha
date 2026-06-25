# Antigravity AI 前端/API 黑盒复验 (Round 3)

## 验证步骤执行情况

1. **启动服务**：成功拉起最新版的本地 API（`jyotish_api_server.py`，端口 5200）和前端开发服务（端口 5173 / 3456）。（**注意**：在复验初期，发现旧版 API 进程仍残留，导致 `/api/chart` 依然返回过时数据。通过 `kill` 终止旧进程并拉起新进程后恢复正常。）
2. **排盘输入**：以 `REDACTED_DATE 14:45:20, lat 36.466667, lon 114.2, tz 8` 为样本进行测试。
3. **网络参数捕获**：经网络请求审计，前端确实通过 `applyCalculationSettingsToPayload` 向后端传递了 `ayanamsa`、`node_mode` 和新增的 `second` 参数。
4. **API 响应检查**：API 正常返回 `success: true`，且其 `birth` 对象中成功带有 `ayanamsa_name`、`ayanamsa_display` 及 `node_mode`。根级别 JSON 同时挂载了完整的 `ai_prompt_pack` 结构（包含 `prompt_zh`、`evidence_snapshot` 等）。
5. **前端界面 UI 检查**：
   - 完整解盘页面底部成功渲染了 `AI Prompt Pack` 面板区块，明确展示 schema 版本号及 prompt_zh 文本。
   - `jyotish-app/ai-chat.js` 会优先从后端传递的 `cd.ai_prompt_pack` 中提取 evidence 并交给用户或 AI 上下文。
   - 左上角的应用头像加载自 `/brand-avatar.png`，其图片实际大小优化至约 417KB，CSS 固定渲染尺寸为 `28px`，符合规范，且不再使用原始 1MB+ 的大图。

## Bug 跟踪表

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|
| **P0/P1** | `jyotish-app/api-bridge.js` <br/> `scripts/jyotish_api_server.py` | - | 之前未下发 `ayanamsa` 参数，且不带 `ai_prompt_pack` 和元数据。 | N/A | **经复验，该问题已被 Codex 彻底修复。** 新版代码参数下发链路贯通，响应体挂载正常，无需额外修复。 |
| **P2** | `jyotish-app/public/brand-avatar.png` | - | 原头像超过 1MB 影响首屏加载。 | N/A | **已被 Codex 修复。** 新头像降至 417KB 并设定了正确的 CSS (28px)。 |

**黑盒复验结论：本次测试涉及的核心功能（参数下发、Ayanamsa 显示、AI Pack 输出、头像）均已按预期完成修复，未发现新的阻断性 P0/P1 缺陷。**
