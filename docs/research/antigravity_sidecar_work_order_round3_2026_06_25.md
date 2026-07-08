# Antigravity AI 副手任务单 Round 3（2026-06-25）

## 角色边界

Antigravity AI 是本项目的外部审计与验证副手。本轮只做黑盒复验、外部对标、开源参考复核和文档化报告，不直接修改核心计算、前端主逻辑、Skill 文件或测试文件。

禁止事项：

- 不要提交、重置、删除、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 token、API key、浏览器登录态、系统钥匙串或远端凭证。
- 不要把本地引擎输出伪装成 JHora、PyJHora、VedAstro、AstroSage、Prokerala 或商业软件结果。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/` 下的实现文件。
- 不要为单个 PDF 样本直接调生产常数、Shadbala 系数或 Dasha 年长常数。

允许事项：

- 可以读取代码、README、报告、测试和浏览器网络请求。
- 可以启动本地 API 与前端做黑盒验证。
- 可以创建或更新 `docs/research/*round3*2026_06_25.md` 报告。
- 可以运行只读验证命令：`python3 scripts/audit_capabilities.py --mode validate`、`python3 scripts/audit_fragments.py --strict`、`python3 scripts/oracle_boundary_audit.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json`。

## 背景

Codex 已完成以下主线修复，Antigravity 本轮要复验这些修复是否真实进入普通用户路径：

- Standalone Swiss Ephemeris Ayanamsa 全局状态修复：`scripts/ayanamsa_utils.py` 统一默认 Lahiri，并允许 Raman/KP 显式切换。
- `/api/chart` 与 `full-reading` 输出 Ayanamsa 元数据和 `ai_prompt_pack`。
- 网页/app 完整解盘页新增 AI Prompt Pack 承载面板。
- AI Chat 优先使用后端 `ai_prompt_pack.prompt_zh`、`evidence_snapshot` 和 `retrieval_plan`。
- 前端保存并下发 `ayanamsa`、`node_mode`、出生秒数 `second`。
- 产品头像已压缩为 `jyotish-app/public/brand-avatar.png`，页头显示尺寸约 28px。

## 对标任务 A：全球同品类能力差距复核

目标：只做事实核验和差距表，不写代码。

对标对象：

- VedAstro / VedAstro.Python：重点核验 596+ calculations、AI/MCP/API、Dasa、Divisional Charts、Ashtakavarga、Matching。
- PyJHora：重点核验 JHora/PVR 体系、Dasha、Varga、Panchanga、Shadbala、许可证边界。
- AstroSage Kundli AI：重点核验普通用户 App 流程、AI Kundli、talk-to-Kundli、Matching、Panchang。
- Prokerala：重点核验在线 birth chart、North/South Indian chart、Varga charts、Dasha/Transit 工具链。

输出文件：

- `docs/research/antigravity_round3_global_product_parity_2026_06_25.md`

报告必须包含：

| 功能项 | 对标产品表现 | 当前项目表现 | 差距等级 P0/P1/P2 | 建议落点文件或接口 |
|---|---|---|---|---|

要求：

- 不要写“全球第一”“排名第一”之类不可验证结论。
- 若写排名，只能写“按开源覆盖度/普通用户可用度/AI Native 承载度的临时分层”，并列明依据。
- 每条建议必须落到具体文件或接口，例如 `jyotish-app/main.js`、`jyotish-app/ai-chat.js`、`scripts/jyotish_api_server.py`、`SKILL.md`、`references/oracle/dasha_shadbala_oracle_cases.json`。

## 开源参考任务 B：Oracle 样本采集可行性

目标：不要复制开源代码，只确认哪些项目适合作为黑盒结果参考。

参考对象：

- VedAstro.Python / VedAstro HTTP API：记录可调用方法、频控、失败模式、适合采集的字段。
- PyJHora / JHora：记录许可证边界、可人工采集的结果类型、不可复制实现的限制。
- Swiss Ephemeris：核验 sidereal mode / ayanamsa 全局状态要求。
- MIT/Apache 替代候选：若发现新项目，先记录许可证、维护状态、能力范围，不直接引入代码。

输出文件：

- `docs/research/antigravity_round3_oracle_feasibility_2026_06_25.md`

必须给出至少 5 个 oracle case 字段模板，其中至少覆盖：

```json
{
  "id": "template_private_oracle_redacted",
  "status": "template_only",
  "source": "JHora/PyJHora/VedAstro/Manual screenshot",
  "birth": {
    "year": REDACTED_YEAR,
    "month": 4,
    "day": 17,
    "hour": 14,
    "minute": 45,
    "second": 20,
    "lat": 36.466667,
    "lon": 114.2,
    "tz": 8
  },
  "settings": {
    "ayanamsa": "lahiri",
    "node_mode": "mean"
  },
  "target": {
    "moon_sidereal_longitude_deg": null,
    "vimshottari_start_date": null,
    "shadbala_components": null
  },
  "verification_note": "Only fill target fields when the value comes from external oracle, not from this repo."
}
```

状态规则：

- `template_only`：只有字段模板，不能用于生产结论。
- `external_verified`：值来自外部软件/API/截图，并在报告中注明来源。
- `local_baseline`：值来自当前项目，只能做回归参考，不能当外部 oracle。
- `sample_only_not_external_oracle`：结构样本，不得用于 Shadbala/Dasha 调参。

## Bug 任务 C：前端/API 黑盒复验

目标：验证 Codex 修复后的网页/app 是否真实承载 Multi-Ayanamsa、出生秒数和 AI Prompt Pack。

建议步骤：

1. 启动本地 API：`python3 scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200`
2. 启动前端：`cd jyotish-app && npm run dev -- --host 127.0.0.1 --port 5173`
3. 浏览器打开 `http://127.0.0.1:5173`
4. 填入用户样本：private birth datetime，lat 36.466667，lon 114.2，tz 8。
5. 在参数页分别保存 Lahiri、Raman、KP，重新排盘。
6. 检查 Network payload 是否包含 `ayanamsa`、`second`、`node_mode`。
7. 检查 API response 是否包含 `birth.ayanamsa_name`、`birth.ayanamsa_display`、`birth.node_mode`、`ai_prompt_pack`。
8. 检查完整解盘页是否出现 `AI Prompt Pack` 面板。
9. 检查 AI Chat 上下文是否优先包含 `【AI Prompt Pack】`、`evidence_snapshot`、`retrieval_plan`。
10. 检查产品头像是否加载自 `brand-avatar.png`，显示尺寸是否约 28px，资源体积是否不再使用原始 1MB+ 大图。

输出文件：

- `docs/research/antigravity_round3_frontend_api_blackbox_2026_06_25.md`

Bug 表格式：

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|

严重度定义：

- P0：普通用户无法排盘、页面崩溃、核心 API 500。
- P1：Ayanamsa/秒数/AI Prompt Pack 参数链路无效，造成计算或 AI 上下文误导。
- P2：文案、样式、导出元数据、头像资源、移动端可用性问题。

## Skill 同步任务 D：Skill 与网页/app 一致性审计

目标：检查 Skill 是否真正承载网页/app 的全部能力，并且不过度宣称准确率。

重点检查文件：

- `SKILL.md`
- `skills/jyotish-engine-modules/SKILL.md`
- `jyotish-app/ai-chat.js`
- `jyotish-app/api-bridge.js`
- `jyotish-app/public/api-bridge.js`
- `scripts/jyotish_engine.py`
- `scripts/jyotish_api_server.py`

重点问题：

- Skill 是否明确要求优先消费 `ai_prompt_pack.prompt_zh`、`evidence_snapshot`、`retrieval_plan`。
- Skill 是否明确读取 `birth_info.ayanamsa_name/display`、`node_mode`。
- Skill 是否承认 Shadbala/Dasha 仍需要外部 oracle 扩充，不夸大为 JHora/PyJHora 绝对校准完成。
- 网页/app 是否存在旧版 prompt 拼接逻辑绕过 `ai_prompt_pack`。
- 是否避免持久化、输出或传播用户个人出生资料。

输出文件：

- `docs/research/antigravity_round3_skill_webapp_sync_2026_06_25.md`

报告必须分三章：

1. 对标
2. 开源参考
3. Bug

Bug 表必须包含严重程度、文件路径、行号、修复建议。

## 普通用户任务 E：成品可用性路径复查

目标：从普通用户视角复查“现在能否作为网页/app 使用”，并指出距离成品还差什么。

复查路径：

- README 的普通用户启动路径是否清楚。
- Trust Center 是否说明本地 API、静态 demo/PWA、隐私与数据边界。
- 无 API 时是否能看到可行动恢复提示。
- 有 API 时是否能完成排盘、保存、导出、完整解盘、AI Prompt Pack 查看。
- PWA/静态 demo 是否没有伪装成完整技法后端。
- 产品头像是否不会撑大布局或拖慢首屏。

输出文件：

- `docs/research/antigravity_round3_user_readiness_2026_06_25.md`

必须给出：

- 普通用户可用结论：`usable_with_local_api` / `demo_only_without_local_api` / `blocked`
- 距离成品项目的缺口清单：P0/P1/P2。
- 准确率边界：基础黄经/D1/D9、Dasha、Shadbala、AI 解读分别给出当前可信度与尚需 oracle 的位置。

## 最终回复格式

完成后在 Antigravity 聊天里回复：

1. 已创建哪些 `docs/research/*round3*2026_06_25.md` 文件。
2. 每个文件的核心结论。
3. P0/P1/P2 Bug 总表。
4. 哪些是 Codex 已修复项，哪些仍需下一轮处理。
5. 不要输出任何密钥、token、登录态、个人隐私字段原文。

最终报告必须使用中文，章节固定为：

- 对标
- 开源参考
- Bug
