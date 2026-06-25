# Antigravity AI 副手工作单（2026-06-25）

目标：把 Antigravity AI 作为并行副手，用于外部样本采集、网页/app 产品审计、skill 同步审计和浏览器验证；Codex 继续负责核心计算修改、测试合并和最终发布判断。

## 当前上下文

- 当前项目已经完成 Multi-Ayanamsa 计算层可验证切换：`full-reading --ayanamsa` 和 `compute_chart_data(..., ayanamsa_name=...)` 会输出 `ayanamsa_name`、`ayanamsa_display`、`ayanamsa_value`。
- 当前项目已经新增 `full-reading.ai_prompt_pack`，用于把 D1/D9/Dasha/Shadbala/Ashtakavarga 证据整理成网页/app 与 skill 可复用的 Prompt/RAG 上下文。
- D1/D9 与 VedAstro 黄经样本已对齐到角秒级范围；但 Dasha 起点和 Shadbala 六分量仍缺 JHora/PyJHora 级外部 oracle，不能宣称已完全校准。
- Antigravity 上次写入的 Shadbala `component_targets` 已被标为 `component_targets_sample_only`，不得当作外部权威样本。

## 对标

- Google Antigravity 的优势是 artifacts、implementation plan、review 与并行 agent 工作流，适合交付可审查的计划、样本、截图和验证记录。
- VedAstro 的优势是 API/Skill/MCP 产品面和 596+ calculation methods、47 ayanamsa、Kuta、Panchanga、prediction API 的宽覆盖。
- PyJHora/JHora 的价值是传统 Jyotish 行为 oracle，适合用于大运、Shadbala 分量、分盘和细分技法的校准样本。

## 开源参考

- VedAstro.Python：MIT；可作为 API/Skill/MCP 产品形态和黄经样本参考。
- PyJHora：AGPL-3.0；只可作为外部行为 oracle 或人工 benchmark，不复制实现代码进本项目。
- jyotishganit：MIT；可作为现代 Python Jyotish 结构和 Panchanga/Dasha/Ashtakavarga 覆盖参考。

## 副手边界

1. 不要读取、复述或使用任何密钥、token、账号凭证。
2. 不要执行删除、重置、强制 checkout、清缓存、移动大量文件等破坏性命令。
3. 不要用 `cat > file`、Python 写文件脚本或 shell heredoc 直接改仓库文件；需要改动时先产出计划和补丁说明。
4. 不要直接重写这些核心文件：`scripts/jyotish_engine.py`、`scripts/oracle_boundary_audit.py`、`references/oracle/dasha_shadbala_oracle_cases.json`、`tests/test_cli_smoke.py`、`tests/test_oracle_boundary_audit.py`、`tests/test_ayanamsa_switching.py`。
5. 不要把本地引擎输出伪装成 JHora/PyJHora/VedAstro 外部 oracle。外部 oracle 必须记录来源、工具版本、ayanamsa、node mode、出生资料、命令或截图/导出证据。
6. 开始前运行 `git status --short`，结束时报告实际读过和建议修改的文件。

## 工作包 A：外部 oracle 样本采集

交付：`docs/research/external_oracle_samples_2026_06_25.md`

任务：

- 收集 3-5 个可复验样本，优先 JHora、PyJHora、VedAstro。
- 每个样本记录出生资料、地理位置、时区、ayanamsa、node mode、Moon sidereal longitude、Vimshottari Mahadasha/Antardasha 边界。
- 若能取得 Shadbala，必须记录 Sthana、Dig、Kala、Chesta、Naisargika、Drik 六分量，不只记录总分。
- 明确哪些字段来自外部工具，哪些字段来自本项目。

验收：

- 只提交研究报告；不要直接改 oracle JSON。
- 如果建议加入 JSON，先给出字段 diff 和证据来源。

## 工作包 B：网页/app Multi-Ayanamsa 与 Prompt Pack 审计

交付：`docs/research/frontend_multiaayanamsa_prompt_pack_audit_2026_06_25.md`

任务：

- 检查 `jyotish-app` 是否把 ayanamsa 设置传到 API/fallback 计算。
- 检查用户界面是否展示 `birth_info.ayanamsa_name/display/value`。
- 检查网页/app 是否能承载并展示 `ai_prompt_pack`，或至少在 AI 解读调用时使用它。
- 输出缺陷表，不直接修改前端。

重点文件：

- `jyotish-app/main.js`
- `jyotish-app/api-bridge.js`
- `jyotish-app/analysis-deep.js`
- `jyotish-app/jyotish-engine.js`
- `jyotish-app/index.html`

## 工作包 C：Skill 同步审计

交付：`docs/research/skill_sync_audit_2026_06_25.md`

任务：

- 比对根 `SKILL.md`、`skills/jyotish-engine-modules/`、`README.md` 与 `scripts/jyotish_engine.py full-reading` 的能力描述。
- 检查 skill 是否写清 Multi-Ayanamsa、`ai_prompt_pack`、Dasha/Shadbala oracle 边界。
- 标出网页/app 有但 skill 没有的能力，或 skill 仍夸大“已校准”的表述。

## 工作包 D：浏览器用户流验证

交付：`docs/research/frontend_user_flow_smoke_2026_06_25.md`

任务：

- 在可启动服务的前提下，验证普通用户路径：出生资料输入、示例盘、设置 ayanamsa、生成完整解盘、导出、Trust Center、AI 解读入口。
- 记录浏览器尺寸、服务启动方式、失败截图或可复现步骤。
- 如果遇到登录、账号、外部密钥问题，只记录阻塞，不尝试绕过。

## Bug 输出格式

Antigravity 的最终报告必须包含以下章节：

1. `对标`
2. `开源参考`
3. `Bug`
4. `交付物`
5. `验证`

Bug 表格格式：

| 严重程度 | 文件路径 | 行号 | 问题 | 修复建议 |
| --- | --- | --- | --- | --- |
| P1 | `scripts/transit_trigger.py` | 61 | standalone 脚本中 sidereal mode 设置被注释，若未统一调用 ayanamsa helper，可能沿用进程全局状态。 | 引入统一 ayanamsa helper，默认 Lahiri，并显式接受调用方传参。 |
| P1 | `scripts/solar_return.py` | 26 | 同上。 | 同上。 |
| P1 | `scripts/muhurta.py` | 617 | 同上。 | 同上。 |
| P1 | `scripts/cmd_muhurta.py` | 31 | 同上。 | 同上。 |
| P2 | `jyotish-app/*` | 待核验 | 前端可能尚未可视化 `ai_prompt_pack`。 | 增加 AI 解读证据面板或在 AI 调用 payload 中传递 Prompt Pack。 |

## 推荐验证命令

```bash
git status --short
python3 scripts/audit_fragments.py --strict
python3 scripts/audit_capabilities.py --mode validate
python3 -m pytest tests/test_ayanamsa_switching.py tests/test_cli_smoke.py::test_full_reading_reports_ayanamsa_metadata_and_ai_prompt_pack tests/test_oracle_boundary_audit.py -q
python3 scripts/oracle_boundary_audit.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json
```

## 完成定义

- 交付的是可审查报告和证据，不是未经确认的大规模代码改动。
- 每个外部数据点都能追溯来源。
- 每个 Bug 都有严重程度、文件路径、行号和修复建议。
- 不扩大许可证风险，不复制 AGPL/GPL 实现。
