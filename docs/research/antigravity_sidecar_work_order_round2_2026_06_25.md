# Antigravity AI 副手任务单 Round 2（2026-06-25）

## 角色边界

Antigravity AI 作为副手，只做外部验证、浏览器黑盒复验、文档审计和报告产出。不要直接修改核心计算文件、前端主文件、测试文件或 Skill 文件。

禁止事项：

- 不要提交、重置、删除或批量格式化文件。
- 不要读取、记录、传播任何密钥、token、浏览器登录态。
- 不要把本地引擎结果伪装成 JHora、VedAstro、PyJHora 或商业软件结果。
- 不要修改 `scripts/jyotish_engine.py`、`scripts/jyotish_api_server.py`、`jyotish-app/main.js`、`jyotish-app/ai-chat.js`、`SKILL.md`。

允许事项：

- 可以读取代码和运行只读命令。
- 可以启动本地 API / 前端 dev server 做浏览器验证。
- 可以创建或更新 `docs/research/*_2026_06_25.md` 报告。
- 可以运行 `python3 scripts/audit_capabilities.py --mode validate`、`python3 scripts/audit_fragments.py --strict`、前端 smoke 只读验证。

## 对标任务

### A. 全球同品类功能差距复核

目标：只做事实核验和差距表，不写代码。

对标对象：

- VedAstro：重点核验 47 Ayanamsa、MCP/API、AI 相关入口、Kuta/合婚、Panchanga。
- AstroSage Kundli：重点核验 AI Kundli、出生盘、Dasha、Matching、普通用户 App 流程。
- Prokerala Vedic Astrology：重点核验 North/South Indian chart、Varga、Dasha、Transit、网页工具链。

输出文件：

- `docs/research/global_product_parity_round2_2026_06_25.md`

必须包含：

- 功能矩阵：功能项、对标产品表现、当前项目表现、差距等级 P0/P1/P2、建议落点文件。
- 不要写“全球第一”之类排名结论；只写可验证的功能差距。
- 每条建议必须落到具体文件或接口，例如 `jyotish-app/main.js`、`scripts/jyotish_api_server.py`、`SKILL.md`。

## 开源参考任务

### B. Oracle 样本采集可行性

目标：不要复制开源代码，只确认哪些项目适合作为黑盒结果参考。

参考对象：

- VedAstro.Python / VedAstro API，优先记录可调用方法、限制、频控、失败模式。
- PyJHora，记录许可证边界、可参考的公开样本类型、不可复制代码的限制。
- Swiss Ephemeris 文档，核验 sidereal mode / ayanamsa 设置要求。

输出文件：

- `docs/research/open_source_oracle_feasibility_round2_2026_06_25.md`

必须包含：

- 开源项目、许可证、可用能力、不能直接采用的原因、建议做法。
- 至少 3 个 oracle case 的字段模板：birth、settings、target、source、verification_note。
- 明确标注哪些值仍是 `template_only`，哪些是 `external_verified`。

## Bug 任务

### C. 前端用户流黑盒复验

目标：验证 Codex 修复后的网页/app 是否真实承载 Multi-Ayanamsa 和 AI Prompt Pack。

步骤：

1. 启动本地 API：`python3 scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200`
2. 启动前端：`cd jyotish-app && npm run dev -- --host 127.0.0.1 --port 5173`
3. 浏览器打开 `http://127.0.0.1:5173`
4. 填入样本：private birth datetime，lat 36.466667，lon 114.2，tz 8。
5. 在参数页保存 Raman 或 KP Ayanamsa，重新排盘。
6. 检查：
   - API payload 是否含 `ayanamsa` 和 `second`。
   - 结果页是否显示后端返回的 `birth.ayanamsa_display`。
   - 完整解盘页是否出现 `AI Prompt Pack` 面板。
   - AI Chat 发送消息时 `chart_context` 是否优先包含 `AI Prompt Pack` 与 `evidence_snapshot`。

输出文件：

- `docs/research/frontend_user_flow_round2_2026_06_25.md`

Bug 表格式：

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|

严重度定义：

- P0：普通用户无法排盘或页面崩溃。
- P1：计算参数切换无效、AI 上下文错误、误导用户。
- P2：文案、样式、可用性、导出元数据不一致。

## Skill 同步任务

### D. Skill 与网页/app 能力一致性审计

目标：检查 `SKILL.md` 是否与网页/app 当前能力一致。

重点检查：

- 是否明确要求优先消费 `ai_prompt_pack`。
- 是否明确声明 `birth_info.ayanamsa_name/display` 与 `node_mode`。
- Shadbala 是否仍保留外部绝对值 oracle 边界。
- 是否避免持久化用户个人出生资料。

输出文件：

- `docs/research/skill_app_sync_round2_2026_06_25.md`

报告必须分三章：

1. 对标
2. 开源参考
3. Bug

Bug 表必须包含严重程度、文件路径、行号、修复建议。

## 交付要求

完成后在 Antigravity 聊天里回复：

- 已创建哪些 `docs/research/*.md` 文件。
- 发现了哪些 P0/P1/P2。
- 哪些项已经被 Codex 当前修复，哪些仍需 Codex 下一轮处理。

不要要求用户授权命令，除非需要运行会修改核心代码、删除文件或访问外部账号的操作。
