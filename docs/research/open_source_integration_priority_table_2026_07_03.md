# 开源项目接入优先级落地表

日期: 2026-07-03

目的: 把仓内已经存在的开源镜像、黑盒基准、官方桥接入口，整理成一张可执行落地表。只写当前仓库里有真实文件可指认的对象，不靠聊天记忆。

边界先钉死:

- 主运行链 source of truth 仍是本仓 `scripts/`、`mcp_server.py`、`references/`、`tests/`、`jyotish-app/`。
- `.workbuddy` 不是 runtime truth。
- `PyJHora` 只能走黑盒输出证据路径，不能把 AGPL 代码抄进 permissive 主链。
- `open_source_reference` 可以进参考层、审计层、提示层，不自动升级成 primary truth。

相关现状依据:

- 主链地图: [docs/research/unique_main_chain_map_2026_07_01.md](<repo>/docs/research/unique_main_chain_map_2026_07_01.md)
- 开源参考层已挂载说明: [docs/research/open_source_batches_runtime_reference_audit_2026_07_03.md](<repo>/docs/research/open_source_batches_runtime_reference_audit_2026_07_03.md)
- 已接入 smoke test: [tests/test_open_source_integrations.py](<repo>/tests/test_open_source_integrations.py)

## 状态定义

- `已接`: 已有代码进入主仓脚本或 runtime reference pack，且有测试/文档证明。
- `半接`: 仓里有镜像或桥接脚本，但还没压进默认主链，或只在参考层可见。
- `未接`: 仓里有资料，但当前没有实际接线点。

## 优先级总表

| 优先级 | 开源对象（仓内真实文件） | 当前状态 | 接哪里 | 用来干什么 | 许可证风险 | 预计几小时落地 |
|---|---|---|---|---|---|---|
| 已接/参考 | `references/open_source_sources/panchanga_api/README.md` `references/open_source_sources/panchanga_api/MCP.md` `references/open_source_sources/panchanga_api/SKILL.md` | 已接入主链；外部镜像仅参考 | `scripts/prashna.py` `scripts/remedies.py` `scripts/jyotish_api_server.py` `scripts/unified_consultation_orchestrator.py` `jyotish-app/main.js` | 现有主链已覆盖 Prashna / Muhurta / Panchanga / Remedies；只保留镜像的方法学参考 | 不可直接复用。镜像 `LICENSE` 为 `All rights reserved`，不得复制实现 | 不新增接线；仅做外部数值证据与显示合同 |
| P0 | `scripts/vedastro_service_adapter.py` `scripts/vedastro_official_mcp_bridge.py` `scripts/diagnose_vedastro_mode.py` | 半接 | `scripts/jyotish_api_server.py` `mcp_server.py` `scripts/unified_consultation_orchestrator.py` | 让 official layer 真正默认参与，而不是只做桥接存在证明；同时把 runtime truth 里的 `official/full/partial/fallback` 说清楚 | 低。这里主要是官方 API/桥接，不是复制外部 GPL 代码 | 3-6h |
| P0 | `references/oracle/artifacts/pyjhora_*` `references/oracle/artifacts/pending_packets/*pyjhora*.json` `scripts/generate_pyjhora_oracle_artifact_manifest.py` | 已接（黑盒证据层） | `scripts/external_oracle_sanity_closure.py` `scripts/oracle_benchmark_inventory.py` `scripts/historical_event_backtest.py` `README.md` | 保留 PyJHora 作为黑盒对照、历史事件回测、数值 sanity，不碰源码复制 | 中高。AGPL 风险不在“调用输出”，而在“复制代码/常量/实现” | 1-3h 做下一轮批量证据清点；8-16h 做更完整事件包 |
| P1 | `references/open_source_sources/jyotishganit/README.md` `references/open_source_sources/jyotishganit/LICENSE` `references/open_source_sources/jyotishganit/jyotishganit/*` | 已接（部分） | `scripts/bhava_bala.py` `scripts/shadbala.py` `scripts/shadbala_advanced.py` `scripts/trimshamsa_d30.py` `scripts/constants/mit_imported_constants.py` `scripts/jyotish_engine.py` | 继续把 MIT 安全算法/常量吸收到本地精度层，尤其是 `Bhava Bala`、`Sputa Drishti`、部分 divisional / constants 对齐 | 低。MIT，且本仓已有显式标注“基于 jyotishganit” | 2-6h 做一轮定点补强；10-20h 做系统 sweep |
| P1 | `references/open_source_sources/jaimini-tropical/README.md` `references/open_source_sources/jaimini-tropical/LICENSE` | 已接（部分） | `scripts/jaimini.py` `scripts/argala.py` `tests/test_open_source_integrations.py` `references/strict-workflow-router.md` | 补强 Jaimini/Arudha/Argala 这条线，让婚恋、事业、财富裁决里对 `AL/UL/Karaka/Argala` 的引用更硬 | 低。MIT | 2-5h |
| P1 | `references/open_source_sources/dashaflow/*` | 已接（部分），但镜像证据不完整 | `scripts/jaimini.py` `scripts/synastry.py` `tests/test_open_source_integrations.py` | 继续利用现成 `Arudha Pada`、附加合婚 kutas、Jaimini 辅助能力；少写重复代码 | 中。当前镜像目录里没看到本地 `LICENSE` 文件，虽在别的 README 中被描述为 MIT，也要补 upstream commit + license 证据 | 2-4h 补许可证锚点；4-8h 做能力扩展 |
| P1 | `references/open_source_sources/VedicAstro/README.md` `references/open_source_sources/VedicAstro/vedicastro/horary_chart.py` `references/open_source_sources/VedicAstro/test_suite/horary_functions_test.py` | 半接 | `scripts/prashna.py` `scripts/kp_system.py` `scripts/ephemeris_backend_probe.py` `tests/` 新 smoke | 作为 KP/Horary 参考源，补“时间问事”与 KP sub-lord 边界，不直接重写主引擎 | 低。MIT | 3-6h |
| P2 | `references/open_source_sources/vedic-astro-skills/README.md` `references/open_source_sources/vedic-astro-skills/antigravity/skills/...` | 半接（参考层已可见） | `mcp_server.py::_existing_interpretation_source_pack()` `references/strict-workflow-router.md` `jyotish-app` prompt pack / guided topics | 主要拿方法学、问答流程、reader validation、rectification 提示结构；不当计算真值层 | 低。MIT | 2-4h |
| P2 | `references/open_source_sources/rishi-ai-mcp/README.md` `references/open_source_sources/rishi-ai-mcp/rishi_ai_mcp.py` | 半接（参考层已可见） | `mcp_server.py::_existing_interpretation_source_pack()` `references/` 主题词映射 `prompt pack` | 拿主题分流、问答组织、relationship/finance/career topic taxonomy；不替代本地 strict workflow | 低。MIT | 2-4h |

## 一条一条展开

### 1. `panchanga_api` → 最该先接

仓内文件:

- [references/open_source_sources/panchanga_api/README.md](<repo>/references/open_source_sources/panchanga_api/README.md)
- [references/open_source_sources/panchanga_api/MCP.md](<repo>/references/open_source_sources/panchanga_api/MCP.md)
- [references/open_source_sources/panchanga_api/SKILL.md](<repo>/references/open_source_sources/panchanga_api/SKILL.md)

为什么优先:

- 你现在已经有 [scripts/prashna.py](<repo>/scripts/prashna.py)、[scripts/remedies.py](<repo>/scripts/remedies.py)、统一入口 [scripts/unified_consultation_orchestrator.py](<repo>/scripts/unified_consultation_orchestrator.py)。
- 缺的不是“再发明一套 Prashna/Remedies”，而是把现有入口压得更完整。
- `panchanga_api` 文档本身就覆盖 `prashna`、`muhurta`、`vrata`、`remedies`，跟你当前三入口结构天然贴合。

最省事接法:

1. `prashna` 入口复用现有 `entry_mode == "prashna"`。
2. `remedies` 继续只吃 `strict_audit_gate` 过滤后的输入。
3. 单独补一个 `muhurta/panchanga` 轻 sidecar，不碰主 chart engine。

### 2. VedAstro official bridge → 必须继续压实

仓内文件:

- [scripts/vedastro_service_adapter.py](<repo>/scripts/vedastro_service_adapter.py)
- [scripts/vedastro_official_mcp_bridge.py](<repo>/scripts/vedastro_official_mcp_bridge.py)
- [scripts/diagnose_vedastro_mode.py](<repo>/scripts/diagnose_vedastro_mode.py)

为什么优先:

- 这不是“有没有桥”。桥已经有。
- 真缺口是: 默认主链什么时候自动用官方层、什么时候 cache 命中、什么时候 free-tier queue、什么时候 fallback。
- 这条一旦压实，web / MCP / skill 才会统一口径。

最省事接法:

1. 继续只走现有 adapter / official bridge。
2. 不新增第二套 VedAstro planner。
3. 把 `runtime_truth` 直接下沉到前端结果页、MCP strict 输出、full-reading。

### 3. PyJHora → 只许黑盒，不许抄

仓内文件:

- [references/oracle/artifacts/pyjhora_oracle_artifact_manifest.json](<repo>/references/oracle/artifacts/pyjhora_oracle_artifact_manifest.json)
- [scripts/generate_pyjhora_oracle_artifact_manifest.py](<repo>/scripts/generate_pyjhora_oracle_artifact_manifest.py)
- 多个 `references/oracle/artifacts/pyjhora_*.txt`

当前定位:

- 它已经在 repo 里，但不是“可接入 runtime 的代码镜像”。
- 它是“黑盒 external evidence 层”。

最省事接法:

1. 继续扩证据包，不扩源码依赖。
2. 让 `historical_event_backtest`、`oracle parity`、`benchmark dashboard` 直接吃 artifact。
3. 不把任何 PyJHora 常量表、实现细节搬进 `scripts/`。

### 4. `jyotishganit` → 已有真吸收，继续吃 MIT 安全部分

仓内文件:

- [references/open_source_sources/jyotishganit/README.md](<repo>/references/open_source_sources/jyotishganit/README.md)
- [references/open_source_sources/jyotishganit/LICENSE](<repo>/references/open_source_sources/jyotishganit/LICENSE)
- 已接痕迹:
  - [scripts/bhava_bala.py](<repo>/scripts/bhava_bala.py)
  - [scripts/shadbala.py](<repo>/scripts/shadbala.py)
  - [scripts/shadbala_advanced.py](<repo>/scripts/shadbala_advanced.py)
  - [scripts/trimshamsa_d30.py](<repo>/scripts/trimshamsa_d30.py)
  - [scripts/constants/mit_imported_constants.py](<repo>/scripts/constants/mit_imported_constants.py)

为什么适合继续接:

- 这条已经不是“设想”。
- 本仓已经明确写了“基于 jyotishganit (MIT License) 算法适配”。
- 所以这里最值钱的是继续定点补 math，不是重新造壳。

### 5. `jaimini-tropical` + `dashaflow` → 已经接进脚本层，值得继续榨干

仓内文件:

- [references/open_source_sources/jaimini-tropical/README.md](<repo>/references/open_source_sources/jaimini-tropical/README.md)
- [references/open_source_sources/jaimini-tropical/LICENSE](<repo>/references/open_source_sources/jaimini-tropical/LICENSE)
- [references/open_source_sources/dashaflow/](<repo>/references/open_source_sources/dashaflow)
- 已接证明: [tests/test_open_source_integrations.py](<repo>/tests/test_open_source_integrations.py)
- 当前脚本:
  - [scripts/jaimini.py](<repo>/scripts/jaimini.py)
  - [scripts/argala.py](<repo>/scripts/argala.py)
  - [scripts/synastry.py](<repo>/scripts/synastry.py)

为什么不是 P0:

- 这条已经有接入 smoke test。
- 现在更大的缺口不在“有没有 A1/A10/UL/Argala”，而在“这些结果有没有被 strict workflow 主裁决强制消费”。

特殊风险:

- `jaimini-tropical` 本地有 MIT `LICENSE`。
- `dashaflow` 当前镜像目录未见本地 `LICENSE`。虽然现有文档多处把它当 MIT 参考，但落下一步代码前，应先补一条 canonical license 锚点。

### 6. `VedicAstro` → 适合做 Horary/KP 辅助，不适合夺主链

仓内文件:

- [references/open_source_sources/VedicAstro/README.md](<repo>/references/open_source_sources/VedicAstro/README.md)
- [references/open_source_sources/VedicAstro/vedicastro/horary_chart.py](<repo>/references/open_source_sources/VedicAstro/vedicastro/horary_chart.py)
- [references/open_source_sources/VedicAstro/test_suite/horary_functions_test.py](<repo>/references/open_source_sources/VedicAstro/test_suite/horary_functions_test.py)

为什么排 P1:

- 你仓里已有 [scripts/prashna.py](<repo>/scripts/prashna.py) 和 [scripts/kp_system.py](<repo>/scripts/kp_system.py)。
- 所以更值钱的是拿它校一遍 Horary/KP 边界，不是整包搬迁。

### 7. `vedic-astro-skills` / `rishi-ai-mcp` → 继续留在参考层，别冒充真值层

仓内文件:

- [references/open_source_sources/vedic-astro-skills/README.md](<repo>/references/open_source_sources/vedic-astro-skills/README.md)
- [references/open_source_sources/rishi-ai-mcp/README.md](<repo>/references/open_source_sources/rishi-ai-mcp/README.md)

当前已接现状:

- 参考层已挂进 [mcp_server.py](<repo>/mcp_server.py) 的 `interpretation_source_pack`
- 研究文档已明确它们是 `not_primary_truth`

为什么不该抢前排:

- 它们更像“问答结构 / topic taxonomy / prompt discipline / reader validation”的参考材料。
- 不适合替代本地 math、official evidence、strict audit gate。

## 最省算力的执行顺序

1. `panchanga_api` → 接 `prashna/remedies/muhurta` 统一入口
2. VedAstro official bridge → 压实默认主链 official 优先
3. `jyotishganit` → 做定点 math 补强
4. `jaimini-tropical` / `dashaflow` → 让已有结果被 strict workflow 真消费
5. `VedicAstro` → 做 Horary/KP smoke + 边界校验
6. `vedic-astro-skills` / `rishi-ai-mcp` → 只升格高价值 reader/rectification 规则
7. PyJHora → 继续只做黑盒证据扩容

## 我给你的直白建议

如果只选 3 项，最值钱的是:

1. `panchanga_api`
2. VedAstro official bridge default closure
3. `jyotishganit` 定点精度补强

原因很简单:

- 第 1 项补“入口能力”
- 第 2 项补“官方优先”
- 第 3 项补“本地精度”

这 3 项一起做，才是真正对用户可用性和严谨度都有立刻收益。
