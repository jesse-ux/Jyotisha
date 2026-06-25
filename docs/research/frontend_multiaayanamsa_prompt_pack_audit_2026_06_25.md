# Frontend Multi-Ayanamsa & Prompt Pack Audit (2026-06-25)

## 审计目标
检查前端（网页/App）是否完全接入并正确呈现了底层的 `Multi-Ayanamsa` 和 `ai_prompt_pack` 能力。

## 发现与缺陷清单

### 1. Multi-Ayanamsa 参数下发缺失
- **文件**: `jyotish-app/api-bridge.js`
- **问题**: 在请求后端的 `fetchAnalysis` 和 `fetchFullReading` 方法中，未将前端设置中的 `ayanamsa` 参数发给 API。这导致用户无论在界面上怎么切换 Ayanamsa，后端都会因收不到参数而使用默认的 `Lahiri` 岁差进行计算。
- **修复建议**: 在 `api-bridge.js` 构建请求体时，明确注入 `ayanamsa: settings.ayanamsa` 参数。

### 2. Ayanamsa 界面展示未对齐后端返回
- **文件**: `jyotish-app/main.js`
- **问题**: 后端已经在 `birth_info` 里吐出了明确的 `ayanamsa_name` 和 `ayanamsa_display` 字段，但是前端在呈现时依然自己利用 `settings.ayanamsa` 加上硬编码进行字符串拼接渲染，且未对齐后端的完整显示逻辑。
- **修复建议**: 优先展示 `chartData.birth_info.ayanamsa_display` 和 `ayanamsa` 度数，保持前后端真理唯一。

### 3. AI Prompt Pack (解盘上下文) 完全未接入
- **文件**: `jyotish-app/api-bridge.js` 和 UI 代码
- **问题**: 虽然底层引擎（`full-reading`）现在支持返回 `ai_prompt_pack`（包含 D1/D9/Dasha/Shadbala/Ashtakavarga 证据），但前端的 AI 解释（如 `buildReadingPrompt`）依旧在使用自己硬拼接的古老上下文逻辑，完全忽略了后端的 Prompt Pack 增强。
- **修复建议**: 在 `buildReadingPrompt` 或者 AI 分析模块，优先读取并植入后端传递的 `chartData.ai_prompt_pack` 作为 RAG 核心知识。

## 审计结论
前端的展示层尚未真正接驳底层强大的 Ayanamsa 切换和高质量的 Prompt 生成。建议后续由 Codex 负责 `api-bridge.js` 和 `main.js` 的修改。
