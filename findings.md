# 印度占星产品化发现记录

## 2026-06-30 VedAstro official hard-override 本轮发现

- 真正需要补的，不是再证明一次“VedAstro 能调用”，而是把 `official -> supplemental -> fallback` 这条权威链压成统一 contract，并让婚恋/事业/财富三条默认工作流都吃同一套结构。
- 本轮之前，`mcp_server.py` 的 strict workflow 已有 `source_priority` 和 `vedastro_official_snapshot`，但缺少用户可消费的：
  - `official_primary_evidence`
  - `local_supplemental_evidence`
  - `fallback_used`
  - `blocked_items`
  - `conflicts`
  因此容易出现“知道官方优先，但看不到究竟哪里官方、哪里本地、哪里冲突”的假闭环。
- 本轮红测很干净，失败都集中在缺少上述字段，而不是旧模块逻辑崩坏。这说明主问题确实是 contract 暴露层，而不是三条主题判定器整体不可用。
- `historical_event_backtest.py` 原先不会带出 `blocked_items` / `conflicts`，导致历史回测明明已触发 strict boundary，外层报告却看不见冲突类型。本轮已补透传。
- `vedastro_evidence_orchestrator.py` 原先虽然拿到了 official full snapshot，但没有把 `section_statuses` 和 route/theme requirement 一起往外带，后续主题裁决无法稳定区分“官方 partial”与“完全 blocked”。本轮已补 `official_section_statuses` 与 `theme_requirements`。
- `high_rigor_workflow_plan_only` 原先只声明 `return_vedastro_catalog_and_source_priority_metadata`，这不足以说明最终真实返回会包含官方主证据/补充/回退/冲突 contract。本轮已改成 `return_official_primary_supplemental_fallback_conflict_contract`。
- `_high_rigor_vedastro_official_summary` 原先只汇总官方 catalog / dynamic selection / report references，不会透传 strict contract 的官方主证据、补充、回退和冲突。本轮已补齐。
- `jyotish_engine.py::_build_vedastro_official_full_snapshot_payload` 原先只输出官方快照层本身，不会把 strict workflow 的 contract 信息带进 `ai_prompt_pack.evidence_snapshot`。这会导致网页/AI 平台虽然拿到官方 snapshot status，却看不到官方优先裁决的真实边界。本轮已开始补这层，至少 relationship strict contract 会被透传到 `vedastro_official_full_snapshot` 节点。
- 本轮 focused verification 已说明：
  - strict workflow contract 层是稳的；
  - orchestrator metadata 层是稳的；
  - high-rigor API summary 层是稳的。
- 仍然存在的真实边界：
  - 大而慢的长回归集合里有耗时测试，需要拆分后继续验证，不应把“慢”误说成“已全绿”；
  - full-reading / prompt pack / 前端直接展示还没完全把三条主题 contract 全量消费完；
  - 当前 `jyotish_engine.py` 透传 contract 时优先复用了 relationship strict evidence，career/wealth prompt/report 面还应继续统一。

## 2026-06-25 Round 25 地毯式碎片扫描前置结论

- 已按用户要求在继续实现前进行整机/多窗口碎片扫描，并生成 `docs/research/whole_machine_fragment_sweep_round25_2026_06_25.md`。
- 当前必须作为实现前置读取的规划文件仍是 `task_plan.md`、`findings.md`、`progress.md`。
- 高价值 Jyotish 资料源不只当前主仓：还包括 `.workbuddy/skills/jyotish-vedic-astrology` 旧 skill 副本、`Documents/星轨talk/engines-repo/jyotish`、`Documents/Codex/2026-06-20/.../engines-repo/jyotish`、Obsidian Jyotish 研究笔记、Downloads 中的 `印度占星.pdf/印度占星1.pdf/Kimi_Agent_高维印度占星师.zip/jyotish_training.agent.final.docx`、以及当前 repo 内 `references/open_source_sources` 和 `benchmarks/jyotish`。
- 隐私边界：Downloads/Obsidian/私人 PDF/完整解盘报告仅作为需求和差距发现来源，默认不提交原文、不复制私人出生资料、不上传完整报告。
- 远端状态：HTTPS `git ls-remote` 可达，`origin/codex/release-hygiene-ci` 远端仍停在 `6338cf5`；本地 `bac3748` docs commit 因 SSH 22 超时尚未确认推送成功。后续需使用 SSH-443 或其他可达方式同步。
- Round 25 副手任务已发布，扫描时已看到部分 `antigravity_round25_*` 报告开始生成，但未满 18+ 前不能视为完成。
- Ashtakoot 结论边界：Round 24 “全 0/瞎编”属于需纠正的过强说法；当前 `scripts/ashtakoot.py` 有非零本地规则，但外部 oracle 仍 0/5，不能声称与 JHora/AstroSage/VedAstro 完全一致。

## 2026-06-28 全仓工作流遗漏扫描结论

- 当前排除 venv/build/dist/cache 后仍有约 1528 个文件；主风险区是 `docs/`、`references/`、`scripts/`、`tests/`、`jyotish-app/` 与 `scratch/`。
- `python3 scripts/audit_fragments.py --strict` 当前返回 `valid: true`、`problem_count: 0`，注册表 89 技法均有引擎/API/前端/测试/脚本中的至少一种产品表面；这说明“registry 声称但完全无入口”的大类问题暂未发现。
- 扫描发现真实遗漏：Functional Benefic/Malefic 后端和 MCP 已接入，但前端 `Technique Audit Table`/Skill Map 一度缺少可见审计行；已通过 `tests/test_frontend_productization.py::test_skill_map_surfaces_functional_benefic_malefic_audit_row` 守门。
- `audit_fragments` 仍标记 3 个脚本候选碎片：`oracle_functional_benefics.py`、`patch_api_tz.py`、`patch_engine_tz.py`。其中 `oracle_functional_benefics.py` 是功能性吉凶 CLI 包装器，应决定是否纳入 registry/quality gate；`patch_api_tz.py` 与 `patch_engine_tz.py` 是会改源码的一次性补丁脚本，不应作为产品工作流留在 `scripts/` 默认面。
- 当前 Git 未跟踪残留 11 个：个人/临时输出 `full_chart_data.json`、`test_dasha.json`、`test_output.json`、`scratch_extract.py`、`scratch_mcp_eval.py`；一次性补丁 `scripts/patch_api_tz.py`、`scripts/patch_engine_tz.py`；个人同步工具 `scripts/sync_to_workbuddy.sh`；测试候选 `tests/test_dasha_raman_truth.py`；测试/研究 artifact `tests/verify-results-v6.1.json` 与 `tests/印度占星实战案例综合验证报告-v6.1-2026-05-03.md`。
- `docs/research/ACTIVE_FRONTS.md` 当前仍列出未闭合项：Vimsopaka semantic mapping for `NEECHA_BHANGA / GREAT_FRIEND / GREAT_ENEMY`，以及 functional role 的 Technique Audit Table rendering 跟进。
- `docs/research/vedastro_parity_matrix_latest.md` 当前 13 行中 `partial=8`、`covered=4`、`missing=1`。P0 未闭合集中在 Tajika Annual、Ayanamsa parity、Report Rendering、MCP/API VedAstro live adapter smoke、Ashtakavarga/Shadbala parity、EventsAtRange/Life Event Graph；Numerology/Non-Jyotish Tools 为 P2 adjacent missing，不属于 Jyotish 主工作流。
- `docs/research/vedastro_fast_path_checklist_latest.md` 现已把 VedAstro 接入进一步落成 6 条执行车道：`official_mcp`、`official_python_bridge`、`rest_adapter`、`local_native_preferred`、`hybrid_router`、`external_evidence_only`。当前官方 live catalog 快照为 `46` 个 tag、`2258` 条 methods/events；高价值默认路由已明确：`MCP/API Surface -> official_mcp`，`Shadbala/Ashtakavarga/Tajika -> official_python_bridge`，`EventsAtRange / Birth Time ML -> rest_adapter`，`D1-D60/Jaimini/Synastry/Prashna -> local_native_preferred`。
- 官方公共 VedAstro MCP 已确认可直连：`https://mcp.vedastro.org/api/mcp/public` 对 `initialize` 与 `tools/list` 返回 200，公开工具面至少包含 `get_current_transits`、`get_dasa_at_time`、`find_best_times_for_task`、`get_horoscope_predictions`、`get_match_report`、`get_horary_prediction` 等；已补本仓薄桥 `scripts/vedastro_official_mcp_bridge.py`，并保持“只做 reachability/tool discovery，不直接改本地 adjudicator score/labels”的边界。与此同时，官方 Python bridge 已确认至少能稳定打通 `GetAllEventDataGroupedByTag`、`PlanetNirayanaLongitude`、`DasaAtTime` 三条高价值方法层。
- `event_judgment_career.md` 之前是明确缺口；现已补进主仓并挂回 `SKILL.md` 与 `quick-reference-guide.md`。因此 career 线当前剩余更偏向裁决细化与报告层，而不是“没有专用骨架”。
- 验证命令：`python3 scripts/run_quality_gate.py --profile quick --skip-frontend-runtime` 通过；`npm run build` 通过；`python3 -m pytest tests/ -q` 通过；`git diff --check` 通过。
- 后续收口结论：`oracle_functional_benefics.py` 已通过 CLI JSON 合同测试进入正式测试表面；`patch_api_tz.py`、`patch_engine_tz.py` 与个人 scratch/output 已归入 ignored `scratch/local`；v6.1 婚恋验证资产已转入 `docs/benchmark/legacy-marriage-v6.1/`；Raman Dasha 草稿保留为 benchmark draft，不再伪装成 pytest。
- 新发现的真实遗漏：relationship strict bridge 原先只识别字符串 `"BadConstellations": "good"`，不识别 nested dict 形态，也不读取 `exceptions` mitigation 文本；已补 `exception_mitigated_match` 与 nested Kuta 归一化，避免 Synastry/Ashtakoot 资产被浅层解析吞掉。

## 开源与本地基线

- `references/open-source-jyotish-scan-2026.md` 已记录可直接复用/对标项目：dashaflow、jyotishganit、panchanga_api、jaimini-tropical、VedicAstro、KPAstroDashboard、vedic_astro_npm、PyJHora、VedAstro、xalen-ephemeris。
- 本轮 GitHub 搜索 `panchanga vedic astrology` 命中 VedAstro/VedAstro、VedAstro/VedAstro.Python、kunjara/jyotish、bidyashish/vedicpanchanga.com、degen0root/panchanga_api、asitsa-dotcom/jyotidarshan、vedic-astrology-starter-kit 等。
- 产品层结论：同品类 Panchanga 不是只给 Tithi/Nakshatra，至少应有日历范围、节日/vrata 标记、吉凶时段、活动筛选、结构化导出与可检索条件。
- 许可证策略：MIT/Apache 可直接复用；AGPL/GPL 仅作行为基准，不能复制代码。

## Panchanga 当前差距

- 当前已有：range API、月历、activity filter、Rahu Kala/Yamaganda/Gulika、Choghadiya、Hora、end times、基础 Ekadashi/Pradosham/Purnima/Amavasya tags、CSV/ICS。
- 仍缺：更丰富的 vrata/festival candidate 标签、按条件检索、导出中保留 condition tags、用户能快速找“适合商业/旅行/修行/避免新开始”的日期。

## 当前实现策略

- 先在 `scripts/muhurta.py` 增加保守规则：基于已有 tithi/nakshatra/vara 数据生成可解释标签。
- 对需要 lunar masa 或太阳入宫才能精确判断的节日，只标记为 candidate，并在说明中提示需要月份/太阳过境确认。
- 前端只增加轻量条件筛选，不改核心 API 数据结构，避免破坏已有工作流。

## Panchanga 本轮结论

- 已实现：Ekadashi/Pradosham/Purnima/Amavasya 之外，新增 Chaturthi、Shashthi、Ashtami、Navami、Akshaya Tritiya candidate、Shivaratri candidate、Pushya/Guru Pushya/Ravi Pushya、Rohini 等保守标签。
- 已实现：`condition_tags` 支持 `has_vrata`、`festival_candidate`、`spiritual_practice`、`auspicious_activity`、`avoid_new_start`、`good_choghadiya`、selected activity good/avoid。
- 产品判断：下一个工作区瓶颈不是算法，而是案例管理。保存星盘、配对、问事已经存在，但缺少多人/家庭分组、关系维度和更强过滤。

## 案例工作区本轮结论

- 2026-06-22 网络检索 `vedic astrology kundli matching app` 命中 JyotiDarshan、VedicAstrologyAndroid、kundali、MyRashifal、CosmicBond 等，产品信号仍然是 Kundli profile + Panchang + matching + reports。
- 当前项目已实现统一案例工作区：星盘、配对、问事都能进入同一列表，支持分组、关系类型、标签、搜索、批量选择、导出和删除。
- 下一个高价值缺口是关系报告模板：同品类 matching workflow 不应只显示 36 分，还要给“关系主题、风险、D9/Kuja/Dasha 证据、行动建议、边界说明”的报告结构。

## 关系工作区本轮结论

- 2026-06-22 网络检索 `ashtakoot kundli matching`、`vedic astrology compatibility matching`、`jyotish matchmaking python`：直接可复用且许可证清楚的合盘内核仍以本地已镜像的 `dashaflow` MIT 代码最贴合；若干新仓库无许可证或只是产品壳，不能直接复制。
- 已实现关系报告模板：把 Ashtakoot 总分/分项、D9 平均质量、Kuja Dosha 平衡、Dasha 同步、强弱 Kuta、风险与下一步建议统一成 `relationshipReport` / `relationship_report` 数据结构。
- 已实现 bi-wheel/composite-style 比较视图：完整出生盘合盘后展示上升/月亮/金星/火星轴线、行星 overlay 宫位、星座关系 tone，以及 Sun/Moon/Venus/Mars midpoint。
- 已实现 `spouse_status_yoga.py` 折叠：`/api/relationship` 返回 `spouse_status_yoga` 与 fragment source；完整合盘上下文生成本人/对方 spouse-status 快照，关系报告、保存配对复盘和 HTML 报告都会展示配偶/婚后成长证据。
- 已实现关系报告打印 polish：HTML 报告中的合盘段落升级为 `relationship-deliverable`，包含结论 hero、证据卡、双人轴线、overlay 表、midpoint、spouse-status、行动列表和边界说明，打印时避免关键卡片拆页。
- 已实现可编辑关系元数据：统一案例工作区可编辑 chart/pair/prashna 的标题、分组、关系类型和标签，保存后刷新列表并保留 JSON 导入/导出形状。
- 2026-06-23 网络/本地扫描报告与 PDF 项目：`vedic-astro-skills` 的 `scripts/report_builder.py` 是最贴合且许可证清晰的本地可复用代码；GitHub 命中的 report/PDF 项目多为无许可证、API SDK、产品壳或 notebook，不适合直接复制为核心管线。
- 已实现后端 PDF 管线：新增 `/api/report_artifact`，限制 HTML 大小、阻断 script/iframe/object/embed/on* 事件属性与 javascript: URL，复用 `report_builder._html_to_pdf` 生成 PDF；Playwright 不可用时返回后端生成 HTML 作为降级工件。
- 已实现前端 PDF 导出：导出菜单新增“导出 PDF 报告”，`exportPDFReport` 将现有单文件 HTML 报告送往后端，下载 `pdf_base64`；若后端 PDF 不可用则下载 `html_base64`。
- 已实现更深关系时机/UL-DK 折叠：完整合盘会从本地 `computeKaraka`/`computeArudha` 和当前 Dasha 中提取 7星制 DK、8星制 DK、UL、7宫主与 Venus/Jupiter/Moon/Mars 触发，把它们折叠进关系报告证据和可读卡片。
- 碎片审计补充：本轮发现前端 UL/DK 函数已存在但未完全闭合到导出与测试；已补 `/api/relationship.relationship_timing`、`uldk-print-grid` HTML/PDF 导出和产品化断言，后续继续优先用 `rg` 排查半接入函数。
- 已实现导出体验 polish：PDF/HTML/JSON/SVG/PNG 导出期间锁定菜单，显示 `aria-live` 状态；PDF 后端渲染不可用时保守下载 HTML fallback，并明确提示用户。
- 已实现 Panchanga 组合条件筛选：用户可同时勾选 vrata/节日候选/修行/活动适配/避免新开始/吉利 Choghadiya，结果按 AND 语义过滤，并展示每个条件的保守说明，避免把候选节日误命名为确定节日。
- 已实现 Panchanga search/details 后端字段：`panchanga_range_report` 返回 `search_summary` 和逐日 `festival_details`，说明候选节日的 tithi/nakshatra/vara basis、confirmation note 与 query examples。
- 已实现前端组合模式与 location-aware 摘要：条件筛选新增“满足全部/满足任一”，摘要展示使用的出生地坐标/时区或手动日出日落来源，节日说明卡在移动端单列展示。
- 已实现计算设置选择器：参数中心可保存 ayanamsa/node/house/sunrise/geocoder 策略，排盘 payload、星盘对象、provenance 和导出报告都会携带；对尚未真正切换底层黄经的选项明确标注为 staged policy。
- 已实现规则/技法检索目录与 API Explorer：后端新增 `/api/technique_catalog` 和白名单 `/api/technique_example`，由 capability audit/technique registry 自动生成 65 个技法目录、domain/status/level 筛选、API endpoint 映射、示例 payload 和可运行样例；前端完整解盘的 Skill workbench 目录卡片可用当前星盘试算，后端不可用时保留原 workbench fallback。
- 产品判断：关系、Panchanga、导出、参数透明度和技法目录已具备普通用户可用基础；下一缺口是规则变体/流派 toggles 与候选碎片归档，让 Yoga/KP/Jaimini/AV 等流派差异不只藏在源码或 JSON。
- 已实现规则变体/流派 toggles 可见化：Yoga、Jaimini Karaka、KP significator、Ashtakavarga、Shadbala、Dasha reference 已进入同一 Calculation Settings 存储和导出链路；其中 Yoga/Ashtakavarga/Shadbala 的 API 结果已开始返回 `rule_variants`，前端 Skill workbench 会展示结果口径。
- 已实现候选碎片真实接入：`curse_yoga_detector.py` 已复用到 `/api/yogas`，返回 `curse_yogas`、风险等级、命中数量和边界提示；`shadbala_advanced.py` 已复用到 `/api/shadbala` 的 `advanced_layer`，补充 Kala VMDH、Yuddha Bala 与 Sputa Drishti 证据，但不覆盖主 Shadbala 排名。
- 已实现 Dasha 叙事/时间线碎片接入：`dasha_analyzer.py` 进入 `/api/dasha.vimshottari_analysis`，补充真实 Mahadasha 起点、当前 Antardasha、Moon Nakshatra/Pada；`dasha_calculator_enhanced.py` 作为五级层级证据层，主周期合同不变。
- 碎片审计发现：候选队列已从 6 个降至 4 个，剩余集中在 reading/orchestrator/bridge/automation 归属；这些更像工作流/代理桥接，需要决定是否属于用户端产品，不能盲目塞进前端。
- 已实现主题化报告编排接入：新增 `thematic_report_orchestrator` registry 条目和 `/api/thematic_report`，将 `report_orchestrator.py` 的五主题叙事、冲突裁决、证据链和 Dasha 时间锚点变成可调用 API；前端 Skill workbench/API Explorer 用 `computeThematicReport` 渲染主题卡。
- 碎片审计结论更新：`reading_orchestrator.py`、`report_orchestrator.py`、`orchestrator_bridge.py` 已有 registry/API/frontend/test 引用链，不再是漂浮碎片；`mevg_automation.py` 作为只读门控状态进入 `/api/case_validation.mevg_gate`；`hermes_bridge.py` 判定为外部个人 agent/WorkBuddy 学习桥，会写用户 home 目录，不纳入占星网页/app 默认产品面。
- 已实现主题报告真实证据链：`/api/thematic_report` 现在区分 `custom_evidence`、`derived_chart_evidence`、`sample_evidence`。传入出生数据或星盘数据时，会 best-effort 调用 chart、dasha、yogas、shadbala、ashtakavarga、relationship、career、Jaimini 模块，生成五主题证据；单个模块失败只进入 warning，不让整份报告不可用。
- 产品判断：这一步解决了“主题报告只有表面叙事/样例证据”的关键问题。下一缺口转向方法透明度：Technique Directory/API Explorer 应给用户可复制 cURL/OpenAPI 片段、方法边界和算法来源说明。
- 已实现 Technique Directory/API Explorer 方法透明度：后端 catalog 返回 `api_docs`、`method_docs`、cURL、最小 OpenAPI operation 和 endpoint notes；前端卡片显示方法摘要/边界/API doc key，试算结果显示 `cURL / OpenAPI` 折叠区。
- 产品判断：技法目录已从“能搜索/能试算”升级为“能复用 API/能解释接口边界”。下一类缺口属于平台与信任层：PWA/桌面包装、隐私/数据位置、术语模式、星历抽象。
- 已实现 PWA/信任中心 MVP：manifest、service worker shell cache、SVG icon、install prompt 状态和 Trust Center 已进入用户端；本地资料可导出，清空本地资料保留二次确认，不自动执行破坏性动作。
- 产品判断：平台层已从普通 Vite 页面升级为可安装/可说明数据边界的 local-first 工具；下一缺口是术语模式与星历抽象，让初学者/专业用户和未来替换 ephemeris backend 都有明确入口。
- 已实现术语模式：入门/专业/梵文优先已进入 Trust Center、tooltip、provenance、JSON/HTML 导出；这补齐了同品类 Jyotish 软件常见的 Sanskrit/英文/本地语言对照体验。
- 产品判断：术语层已不再只是点击 glossary，而是可配置的解释口径。下一缺口继续集中在平台化交付：PWA 之后的 Pake/Tauri 桌面包装说明，以及 SwissEph/VedAstro/Xalen 等星历底座替换可行性。
- 2026-06-23 首次使用对标补充：Hora Prakash 的无注册/PWA/隐私本地化、VedAstro 的 API/skill/chat/API doc surface、Maitreya/HinduVahini 类桌面/功能软件都说明，同品类产品不能只堆计算标签，首屏必须让用户知道“如何开始、环境是否可用、无 API 时能做什么、已有星盘如何导入”。
- 已实现首次使用与空状态路径：首屏提供运行健康检查、示例盘填入、已有星盘导入聚焦；本地星盘库空状态从静态说明改为引导用户用示例盘/导入/手动输入生成第一张盘。
- 产品判断：这一步补的是普通用户的第一分钟体验，降低“页面功能很多但不知道从哪里开始”的风险。下一缺口不再是静态入口，而是真机/浏览器首跑验证：桌面和移动端是否无重叠、示例盘能否生成、健康检查失败文案是否能指导启动本地 API。
- 官方安全口径补充：OpenAI API key 属于 secret，不应出现在浏览器/app 客户端代码、localStorage、URL 参数或公开仓库；Jyotish AI 聊天应经由服务端 `/api/chat` 或本地后端代理读取服务端 `OPENAI_API_KEY`。
- 已实现 AI/导出信任层 polish：AI 聊天默认回复改为服务端密钥处理说明；PDF 导出失败或后端 PDF 渲染不可用时保守导出 HTML，并提示 Trust Center 健康检查与 Python API 启动命令。
- 产品判断：首次使用路径之后，普通用户的下一类卡点是“PDF/AI 点击失败但不知道为什么”。现在错误恢复已经从技术异常变成可行动路径；下一缺口可以转向星历抽象可行性，把 SwissEph/VedAstro/Xalen 的长期替换边界从文档推进到可测试探针。
- 已实现星历抽象可行性探针：`scripts/ephemeris_backend_probe.py` 会输出 `candidate_backends`、`license_posture` 与 `replacement_readiness`，把 `swisseph_python` 标为 primary，`swisseph_wasm` 标为 fallback，`xalen_ephemeris` 标为 spike_only，`vedastro` 标为 product_api_benchmark，`pyjhora_benchmark` 标为 benchmark_only。
- 许可证与替换结论：当前不能把 xalen/VedAstro/PyJHora 说成已替换核心计算。SwissEph 仍是生产黄经来源；xalen 需要本地 adapter 和 parity matrix；VedAstro 适合作为 MIT 产品/API 对标；PyJHora 因 AGPL 只做行为基准或 oracle，不复制实现。
- 产品判断：下一步不应继续堆 UI 标签，而应建立后端 adapter contract 与 longitude parity matrix，要求 Sun/Moon/Asc/Rahu/Ketu 和 Panchanga 边界案例在可接受 delta 内，才允许非 SwissEph 后端进入运行时选择。
- 已实现后端 adapter contract：`scripts/ephemeris_adapter_contract.py` 定义 `EphemerisAdapterContract` 与三组 `PARITY_CASES`，复用当前生产 `swisseph_python` 计算 Sun/Moon/Asc/Rahu/Ketu baseline，并保留 `candidate_backend` 插槽。
- 接入标准：任何后续 SwissEph WASM、xalen 或 VedAstro 服务边界都必须输出相同字段，包括 `ayanamsa_value`、sidereal longitude、speed、`retrograde`、backend metadata，并通过 `longitude_delta_arcsec` 阈值后才能进入运行时设置。
- 候选 adapter gate 结论：本地没有 xalen 可执行来源；SwissEph WASM 资产可用但包许可证分别为 `AGPL-3.0` 与 `GPL-3.0-or-later`，因此只能作为本地 fallback/实验路径，不能无审查地进入商业桌面/PWA 分发叙事。
- 真实浏览器点击级 smoke 结论：静态产品化断言和 curl runtime smoke 仍不足以发现用户点击路径问题；新增 `tests/run_frontend_click_smoke.py` 后，真实覆盖了示例盘生成、AI chat、HTML 导出、Transit、合盘、问事，并发现 HTML 报告导出实际会因 `sub_lord is not defined` 失败。
- HTML 导出 Bug 根因：`jyotish-app/jyotish-advanced.js` 的 `computeNakshatraAdvanced` 定义 `subLord`，但返回对象误用 `sub_lord,` 简写；真实用户生成星盘后导出 HTML 会在构建 extras 时抛错。已修为 `sub_lord: subLord`，并增加测试守门。
- 产品判断：当前桌面在线 happy path 已有真实浏览器守门；下一缺口是移动端/离线/PWA 安装、无 API 启动失败、PDF fallback 与浮层遮挡等更接近普通用户环境的交互守门。
- 移动端点击守门结论：390px 视口下 AI FAB 原本会被星盘 SVG/行星表截获，且 chart/table 容器会把页面撑到 528px。真实用户在手机上可能无法打开 AI 面板。已将移动 FAB 放到左侧安全区、AI panel 锁定 `100vw`，并收紧 chart/table 容器宽度。
- 离线/无 API 结论：无 API 时前端可以通过浏览器 fallback 生成基础星盘，健康检查会显示 `npm run web` 与 `python3 scripts/jyotish_api_server.py` 恢复路径；console 中的 `ERR_CONNECTION_REFUSED` 是预期 API 探测噪声，click smoke 已分入 `expected_offline_console_errors`。
- 桌面包装探测结论：本机 Rust/Node 基础可用，但未安装 `pake`/`tauri` CLI；`xcodebuild` 只有 CommandLineTools，不能视为 macOS signing/notarization ready。Pake 上游 GPL-3.0，Tauri 仍需 sidecar 生命周期、权限、签名/公证策略；当前不能声称桌面包已可发布。
- PDF fallback 点击结论：真实用户点击 PDF 导出时，如果后端 PDF 渲染不可用，前端必须明确“已改为导出 HTML 报告”，并提供 Trust Center 与本地 API 启动路径。`run_pdf_fallback_smoke` 现在把这条路径纳入浏览器守门。
- PWA 离线 shell 结论：service worker 控制后的二次 reload 可以保留首屏 shell；离线状态下 JS module/API 请求会产生 `ERR_FAILED`，这是预期离线噪声，脚本单独放入 `offline_shell_expected_console_errors`，避免把真实 JS error 混进去。
- 移动端长标签结论：Complete/Vargas/Synastry/Prashna/Transit Compare 已可在 390px 视口真实切换；下一类风险转向导入 PDF/文本星盘、保存案例库、移动端导出菜单和 Trust Center 长内容。
- 报告 artifact 契约结论：只返回 `html_base64/pdf_base64` 不足以支撑普通用户体验；后端必须显式返回 `artifact_status`、`primary_artifact`、`download_filename`、`download_mime`、`fallback_reason`、`user_message` 与 `next_action`，前端才能在 PDF 不可用、API 未连接或 HTML fallback 时给出一致的下载名和恢复动作。
- 验证结论：runtime smoke 现在会检查 report artifact 的状态、下载文件名和用户指引，不再停留在“有 base64 就算通过”的浅层检查。下一类高风险用户路径是导入 PDF/文本星盘、保存/重开案例库，以及移动端长内容中的导出菜单和 Trust Center。
- 导入/案例库结论：文本星盘导入、填表、生成盘、保存本地星盘、重开保存星盘、工作区保存与案例库导出已经进入真实浏览器守门；这类路径不能只看按钮存在，因为之前 smoke 本身先后暴露了隐藏 logo 和未切换 provenance tab 两个真实选择器/可见性问题。
- 下一风险：移动端已经验证过长标签切换，但还没有专门验证导出菜单、Trust Center 长面板、健康检查、本地资料导出/安装说明在 390px 视口下是否可读、可点击、无横向溢出。
- 移动 Trust Center 结论：健康检查 API 成功不等于用户能看到成功；原实现会在 `renderAll()` 后把“健康检查通过”覆盖回 PWA 默认说明。状态文案必须由 runtime health 派生，才能在移动端和普通用户长面板中稳定可见。
- 移动工作区布局结论：案例库内部控件在 390px 视口下会因 `case-workspace-counts`、`case-workspace-controls` 等块宽度叠加父级 padding 产生右侧溢出。移动端不仅要让主 grid 单列，也要给嵌套工作区控件 `min-width:0` 和单列/最大宽度约束。
- 质量门结论：长链路浏览器 smoke 必须有命令级超时和进程快照，否则失败时容易留下 API/Vite 子进程并让用户不知道卡在哪里。`--timeout` 与 `--frontend-click-timeout` 已成为默认质量门的一部分。
- 文件导入结论：粘贴文本通过不代表文件上传也可用；真实浏览器守门需要覆盖 `set_input_files`、文本文件读取、PDF API 抽取失败和移动端上传入口触控尺寸。移动端“上传文件”低于 40px 时虽然视觉可见，但不适合普通用户触控。
- 下载稳定性结论：在长链路 `--mode all` 中仅靠 `page.on("download")` 收集文件名会有偶发遗漏；关键导出动作应使用 `page.expect_download()` 包裹点击，才能把案例库导出失败和测试竞态区分开。
- 启动路径结论：普通用户不应同时面对“npm run web / npm run dev / python API / PWA / Pake / Tauri”多套入口。当前 README 和质量门失败摘要已统一为“先网页、再本地 API、然后 Trust Center 健康检查”，并明确 PWA 只包装网页壳。
- 术语一致性结论：可复制命令属于 README/质量门摘要，应用内恢复文案属于普通用户语言。界面只给“普通用户启动路径 / 网页服务 / 本地 API 服务 / PWA 安装壳 / Trust Center”，避免把用户推回开发者命令细节；真实浏览器 mobile-trust smoke 已验证新 Trust Center 成功文案可见。
- 下一风险：质量门已经覆盖真实浏览器全链路，但默认 full click smoke 成本较高。需要把 fast/default/release 三层验证写清楚，确保主动迭代时不跳过核心路径，发布前仍跑 `--mode all`。
- 整机初扫发现：当前项目并非唯一资料源。高相关目录包括 `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology`、`/Users/wuyongnaren/Projects/星轨资料恢复/17-Skills技能库/jyotish-vedic-astrology`、`/Users/wuyongnaren/Projects/星轨资料恢复/25-相关Skills补充/jyotish-vedic-astrology`、`/Users/wuyongnaren/engines-repo/jyotish`、`/Users/wuyongnaren/Documents/星轨talk/engines-repo/jyotish`、`/Users/wuyongnaren/WorkBuddy/2026-06-09-20-03-34/jyotish-fragments`、`/Users/wuyongnaren/文件仓库/印度占星文章`、`/Users/wuyongnaren/文件仓库/中外🔮占星/国外占星/印度占星书`。
- 整机初扫还发现多份可能包含遗漏结论的历史报告：`.workbuddy/brain/*/印度占星Skill全面审计与能力评估报告-v3.0.md`、`.workbuddy/brain/*/jyotish_improvement_plan.md`、`WorkBuddy/2026-06-10-21-30-47/印度占星Skill_真实Bug与遗漏清单_v6.1.11.md`、`WorkBuddy/2026-06-10-21-30-47/开源印度占星项目搜索报告.md`、`WorkBuddy/2026-06-12-15-22-12/vedic-astrology-open-source-research.md`。
- 云端探测结论：SSH `git ls-remote` 因 22 端口连接超时失败；HTTPS `git ls-remote https://github.com/732642856/yinduzhanxing.git` 成功，远端 refs 包含 `refs/heads/main`、`refs/heads/codex/release-hygiene-ci`、tags `v6.0.47` 至 `v6.0.52`。GitHub REST API 匿名访问被 rate limit，因此云端字符级审计应使用 HTTPS git mirror。
- 历史遗漏报告共识：旧报告反复指出的非表层缺口不是 UI，而是专业技法深度和 benchmark：Ashtakavarga PAV/Prashtara/Kakshya/Yoga Pinda、Bhava Bala、Navatara/Tara Bala、Kantaka Shani、Pushkar Navamsa、Ishta/Kashta Phala、36 Sahams、Tajika 强度体系、KP Horary/Prashna 裁决、Muhurta 求解器、Vimshottari 多起算点、精微分盘 D24/D30/D60 深度解读。
- 许可证边界：历史报告中 `VedicAstro`、`dashaflow`、`vedic-astro-skills`、`happyalu/panchang-muhurt` 标记为 MIT 或可复用；`PyJHora`、`vedic-calc` 标记为 AGPL/GPL 参考/benchmark-only，不能直接复制进当前产品。
- 覆盖矩阵结论：`scripts/sade_sati.py`、`scripts/kakshya.py`、`scripts/bhava_bala.py`、`scripts/prashna.py`、`scripts/varshaphala.py` 说明旧缺口里很多已进入后端/API；但 `Prashtara`、`Yoga Pinda`、`Panchavargiya`、`Sayanadi` 仍没有 registry/API/frontend 闭环。
- 云端/本地差异结论：GitHub `codex/release-hygiene-ci` 云端快照只有 720 文件，本地工作区 1525 文件且包含大量 build/cache 产物和未提交开发文件。后续判断“是否遗漏”必须以当前工作区 + 云端 mirror + `.workbuddy/skills/jyotish-vedic-astrology` 三方对照，不能只看当前目录。
- 下一实现判断：Ashtakavarga Prashtara/Yoga Pinda 是优先级最高的真实遗漏，因为当前项目已具备校准后的 BAV/SAV 与 Kakshya，但缺少专业软件常见的源贡献展开和 Yoga Pinda 层；本地 `dashaflow/ashtakavarga.py` 是最贴近可复用参考。
- Ashtakavarga 复核结论：当前代码并非完全没有 Prashtara，`calc_prastara_av()` 已存在；真实缺口是 PAV 形状、Yoga Pinda、API summary、Skill workbench 和 registry 没有形成一等产品闭环，导致用户看不到专业贡献追溯。
- Ashtakavarga 本轮修复：新增 `calc_yoga_pinda()`，让 Yoga/Shodhya Pinda 可被 API 与测试直接调用；`/api/ashtakavarga` 返回 `yoga_pinda_summary`；前端 Skill workbench 新增 Yoga Pinda 卡片与校验标签；registry 新增 `ashtakavarga_yoga_pinda` 条目并更新主 Ashtakavarga covered 状态。
- Ashtakavarga 剩余边界：当前 Yoga Pinda 复用项目既有 v2.1 Shodhya Pinda 权重口径，并已明示 validation note；若后续要对齐更严格传统流派，需要引入外部书例/benchmark，而不是把当前权重伪装成全部流派通用标准。
- 下一高价值遗漏：Sripathi/Placidus 房宫算法切换。当前设置层已有 house policy 叙事，但用户还不能验证切换后房宫、Bhava Chalit 与报告证据如何变化；应先地毯式查本地 `bhava_chalit`、历史碎片和开源 references，再补 parity tests/API provenance/frontend selector。
- Antigravity/VedAstro 复核结论：Antigravity 临时 SDK 报告中 D1/D9 对齐结果有效，可增强对当前基础排盘和 Navamsa 映射的信心；但报告未成功取得 VedAstro Shadbala/Dasha，因此不能用它来判定当前 Shadbala 或 Vimshottari 实现错误。
- 过期结论纠正：当前项目已经支持 `--second`，前端/API/wrapper 也能保留秒级时间；Shadbala 主输出已改为 v6.9.15 absolute Rupas，用户样本总量约 55.1437、Sun 约 9.7035，不再是旧报告中的 1.7-3.5 归一化档。
- Dasha 差异边界：用户 PDF 目标起点 `1986-05-18` 与当前引擎 `1986-05-23T22:45:10` 仍相差约 5.948032 天；`scripts/dasha_reference_audit.py` 显示秒级输入和年长常数不能单独解释，应继续比较外部 oracle 的 Moon sidereal longitude、ayanamsa 与 Vimshottari 起算口径，不能为单份 PDF 直接调生产常数。
- 分盘回归 Bug：`scripts/divisional_charts_extended.py` 的 D81/D108/D144、custom、composite varga 曾可能生成超过 360 度的中间黄经并导致 sign index 越界；已统一用 `_position_parts()` 归一化，并增加回归测试。
- Level 3 外部解盘审计：附件解盘的 D1/D9 和 Saturn/Ketu 大运方向可参考，但存在 Sun Ashwini Pada、Venus combustion、retrograde、Ashtakavarga SAV 与 True/Mean Node 口径混用等可计算错误，已记录到 `docs/research/level3_reading_audit_2026_06_25.md`。
- 尊严状态 Bug：外部解盘触发了真实产品问题，`scripts/jyotish_engine.py` 与前端 fallback 原本只把 Exalted/Debilitated/Own Sign 标出来，导致 Jupiter in Virgo 被显示成“中性”。已按行星对星座主星的态度输出 `入友/入敌`，并补 CLI/前端测试。
- Skill 同步结论：网页/app 主线已修复的 D81/D108/D144 分盘归一化和 D1 友敌尊严标签需要同步到 skill 分发层，否则不同窗口/自动化可能继续使用旧副本。本轮已同步 `skills/jyotish-engine-modules/scripts/divisional_charts_extended.py`，并修正根 `SKILL.md` 中“全球第1”“1200/1200 Virupas校准”等过强/过期口径，新增测试防止再次漂移。
- 公开演示环境结论：静态 demo/PWA 不能伪装成完整本地 API 应用。首屏和 Trust Center 现已展示“静态演示模式”能力边界：可直接体验出生资料输入、基础 D1/D9、术语模式和 Trust Center；PDF/HTML 报告、高级技法、真实案例复验、AI 解读代理需要本地 API。`deployment_preflight.py` 输出 `static_demo_boundary_visible`，发布前会阻断边界文案缺失。
- Dasha/Shadbala oracle 边界结论：新增合并审计后，当前可重复报告显示 Dasha 用户 PDF 起点差异仍为 `1986-05-23T22:45:10` vs `1986-05-18`、所需 Moon 偏移约 `0.01206283°`；VedAstro SDK 黄经样本已进入 `longitude_cases`，本地 Moon 与 VedAstro Moon 差约 `26.2254` 角秒、全 9 项均在 120 角秒阈值内，因此基础落座/D9 可信度更高，但不足以解释 Dasha 起点差异；Shadbala 输出已是 v6.9.15 absolute Rupas，但外部目标仍缺六分量拆分，因此 `production_tuning_recommended=false`，不能把单份 PDF 或全局缩放当成校准完成。
- Antigravity 并行修改审计：其写入的 Shadbala `component_targets` 是本地结构样本，不是 JHora/PyJHora 外部权威样本；`scripts/oracle_boundary_audit.py` 已将这类目标标为 `component_targets_sample_only` / `sample_only_not_external_oracle`，防止误宣称绝对值校准完成。
- AI Native 差异化承载：`scripts/jyotish_engine.py full-reading` 已输出 `ai_prompt_pack`，将核心星盘、Dasha、Shadbala、SAV、D9、错误/边界整理成 RAG/Prompt 上下文。该层用于网页/app 和 skill 的大模型解读，不替代底层计算，也不硬编码断语。
- Antigravity 副手定位：官方 Antigravity artifacts/implementation plan 适合做可审查副任务；结合公开安全事件与用户本地密钥风险，本项目把它限制为 oracle 样本采集、网页/app 审计、skill 同步审计和浏览器用户流验证，不让它直接重写核心引擎或执行破坏性命令。
- 新发现的下一修复点：`scripts/transit_trigger.py`、`scripts/solar_return.py`、`scripts/muhurta.py`、`scripts/cmd_muhurta.py` 中 sidereal mode 设置被注释后依赖进程全局状态；下一步应引入统一 ayanamsa helper，默认 Lahiri，并允许调用方显式覆盖。
- Ayanamsa 全局状态根因确认：Swiss Ephemeris 的 sidereal mode 是进程全局配置，`FLG_SIDEREAL` 不会自动指定 Lahiri。红灯测试显示在全局切到 Raman 后，Transit/Muhurta/Solar Return 默认输出会漂移约 `1.446°`。已通过 `scripts/ayanamsa_utils.py` 统一在每次 sidereal helper 调用前设置口径，默认 Lahiri，并允许调用方显式覆盖。
- Yoga 准确率脚本修正：`scripts/validate_yoga_accuracy.py` 原先在 `FLG_SIDEREAL` 后又手动减 ayanamsa，存在双重扣减风险；现改为显式 Lahiri sidereal flags，并直接使用 SwissEph 返回的恒星黄经，避免准确率报告被验证脚本自身污染。
- 前端联调结论：`/api/chart` 是普通用户最常走路径，必须直接返回 Ayanamsa 元数据与 `ai_prompt_pack`，不能只让 CLI `full-reading` 拥有 AI Native 上下文。当前已补 `/api/chart.ai_prompt_pack`、完整解盘面板和 AI Chat 上下文优先级。
- 产品头像结论：原图 1046×1024、约 1.4MB，作为页头头像和 PWA 图标过大；已压缩到 512px、约 417KB，并把页头显示尺寸收敛到 28px。
- Antigravity Round 2 边界：副手适合继续做全球产品黑盒复验和 oracle 样本可行性，不适合直接改核心计算或读取密钥；任务单已把输出限定在 `docs/research`，避免与 Codex 当前实现冲突。
- Antigravity Round 3 派工结论：副手下一轮不再重复旧的“前端未接 Prompt Pack”静态结论，而是以黑盒复验为准，检查 Network payload、API response、完整解盘面板、AI Chat 上下文、头像资源体积和普通用户可用路径；仍禁止读取密钥或修改核心代码。
- Antigravity Round 4 派工结论：副手要从“缺 oracle”的抽象结论进入“每个 template case 缺什么、从哪里采、何时能升 external_verified”的执行层；当前 5 个模板全部保持 `template_only`，审计脚本会输出缺失字段并保持 `production_tuning_recommended=false`。
- Dasha/Shadbala 采集队列结论：`scripts/oracle_collection_queue.py` 当前从 5 个 template case 生成 5 个 `ready_for_collection` 任务，但 `ready_for_calibration` 仍为 0、`production_tuning_allowed=false`。这把下一步从“讨论准确率差距”推进到“逐字段采 Moon longitude、Vimshottari boundary、Shadbala 六分量外部真值”，同时继续阻止用本地输出或模板值调生产常数。
- 质量门结论：release profile 不应只报告 `production_tuning_recommended=false`，还要给维护者/副手可执行的采集清单；因此 `ORACLE_COLLECTION_QUEUE_CMD` 已跟随 oracle boundary audit 运行，并被 README/静态测试锁定。
- Evidence packet 结论：仅有采集 task 不够，必须给每条任务一个可填写证据包，要求 `tool_name`、`source_artifact`、`ayanamsa`、`node_mode`、`timezone` 等元数据，并把 target placeholders 与 missing fields 逐项绑定。这样后续录入时可以审计“这个值来自哪里”，而不是只看数字。
- Shadbala 防线结论：凡是缺 `target.shadbala_components` 的任务，证据包都会标记 `reject_global_shadbala_scaling`，防止为了贴合一个总分而引入粗暴倍乘系数。
- Evidence validator 结论：采集队列还需要第二道门来验证“已填写的证据包能否晋级”。`scripts/oracle_evidence_validator.py` 当前会拒绝空 metadata、缺 `source_artifact`、未填 target placeholders、非 `external_verified` 状态，以及含 `Local Engine`/`this-repo`/`scripts/jyotish_engine.py` 等本仓库来源的 artifact。
- 质量门覆盖结论：只在 release profile 运行 oracle 队列不足以支撑日常主动迭代；`CORE_PYTEST_TARGETS` 已纳入 collection queue 和 evidence validator 测试，使 quick gate 也能发现采集队列/证据包漂移。
- Round 7 后续审计发现：如果未来人工把 oracle JSON 某条 case 升级为 `external_verified`，旧队列生成器会重新生成 draft evidence packet，导致“已填外部真值仍过不了 validator”。已修为保留 `evidence_packet.status/metadata`，并用 `target_fields` 固定目标字段集合。
- 对标差距结论：相对 VedAstro/PyJHora/JHora，当前最实质缺口不是基础 D1/D9，而是 Dasha/Shadbala 外部真值样本库、合婚/Koota/Panchanga 的 API/产品深度、以及普通用户一键使用/校准状态可视化。PyJHora 因 AGPL 只能黑盒参照，JHora 因闭源只能截图级人工采集。
- 2026-06-26 Round 28/29 接力结论：Round 28 的 30 份研究报告已回到主仓待归档区，覆盖全球开源排名、PyJHora/JHora 广度差距、MIT 可复制资产、Dasha/Panchanga/Muhurta/Synastry/Shadbala/Jaimini/KP/Varga/Yoga 深度路线、skill 同步缺口、真新增技法最小集与 Round29 Top100；同时新增 `docs/research/antigravity_sidecar_work_order_round29_2026_06_26.md`，将副手任务继续加压到 skill 全量补齐差距、API/CLI/前端隐藏能力、整机碎片复用第二轮、云端同步白名单、外部 oracle 精度闭环与 Round30 Top120。
- 2026-06-28 真实用户全功能 QA：使用 `REDACTED_DATE REDACTED_TIME`、河北REDACTED_PLACEREDACTED_PLACE矿区近似坐标 `36.4467,114.2` 跑完 CLI/API/前端点击/质量门矩阵。能力注册表 89 项有效、碎片审计 37 CLI + 41 API 无未注册高价值候选、前端 `--mode all` 浏览器点击通过、quick quality gate 通过；正式报告见 `docs/research/sample_user_full_function_qa_REDACTED_YEAR_redacted_place_2026_06_28.md`。
- 本轮 QA 真 bug：`jyotish_engine.py muhurta` CLI 因 Sun/Moon tuple 进入 `calc_tithi` 崩溃；`varga-full --divisions ... D81/D108/D144` 仍走旧 `scripts/varga.py` 而失败，尽管 `--custom 81` 可算；`/api/remedies` 对数值型 Shadbala 简写会 500，应归一化或返回 400。
- 本轮 QA 边界结论：`/api/technique_example` 用目录官方 example payload 可 200，普通出生资料直打 400 是合同误用而非后端坏；`db-stats` 返回数据库不存在，说明入口可用但本机 celebrity/validation DB 数据源缺席；外部 JHora/PyJHora/VedAstro oracle 精度仍未因此闭环。
- VedAstro 强制雷达边界：官方 Events Builder 暴露 `SearchEvents / GetEventTiming / ListEventTypes` 三个事件端点、400+ 预定义事件和 `Scan precision (hours)`，API/Python surface 继续按 600+/596+ 计算节点理解。本项目不硬复刻 596 个函数，而是把 VedAstro range scan 作为 `career/relationship/finance` strict workflow 的必需外部高频 timing radar；缺失时进入 `vedastro_range_scan_missing` 和 Technique Audit blocked 行，不能再静默跳过。
- VedAstro Adapter MVP 方案 A 结论：当前已完成工程闭环而非官方实网闭环。adapter range scan 会产出可审计 provenance（request/response SHA-256、called_at、endpoint_host、artifact_path、retry metadata、allowlist/raw/filtered event counts），`/api/vedastro/status` 与 Trust Center 能显示安全配置状态，`vedastro-live` profile 在未配置 endpoint 时受控 blocked 并通过默认 CI。只有配置 `VEDASTRO_API_ENDPOINT` 和 `VEDASTRO_ENABLE_NETWORK=1` 后，才能把状态从 `network_execution_disabled/service_endpoint_not_configured` 推进到真实 VedAstro live smoke；在此之前不得宣称官方 VedAstro 事件雷达已经实网验证。
- VedAstro 普通用户入口结论：用户侧可用的定义不是“adapter 存在”，而是“生成星盘后能点击按钮、使用当前出生资料、选择领域/日期范围、看到返回状态和边界”。本轮已把这一层落在 Trust Center `VedAstro Range Scan` 面板和 `/api/vedastro/range_scan`；未配置 endpoint 时用户看到 blocked，配置官方 endpoint 与网络开关后同一按钮会走实网调用链。

- 2026-06-29 高严谨默认入口复用结论：项目内已有可直接复用的生时校正、历史事件回测、主题推运和 VedAstro 官方证据层，不应重新造算法。关键资产包括 `scripts/birth_time_rectifier.py`、`jyotish-app/rectification-engine.js`、`scripts/historical_event_backtest.py`、`scripts/reading_orchestrator.py`、`scripts/report_orchestrator.py`、`scripts/orchestrator_bridge.py`、`scripts/vedastro_evidence_orchestrator.py`、`scripts/vedastro_official_capability_runner.py`。新增统一入口应做胶水层：VedAstro official snapshot/catalog first -> rectification gate -> historical event backtest -> thematic report，而不是把 641 callable 暴力全跑。
- 2026-06-29 省算力边界：`/api/high_rigor_workflow` 的 Technique Explorer 样例必须使用 `dry_run`，否则目录页会触发重型 VedAstro/full-reading 链路。真实用户提交不带 `dry_run` 时才执行完整高严谨工作流。这个设计同时满足“用户可直接用”和“不要浪费算力”。
- 2026-06-30 VedAstro 641 项轻量映射表结论：`official_full_capability_catalog` 现在为每个官方 callable 标注 `domains / execution_policy / priority`，并聚合出 `domain_routing`，覆盖 `career / marriage / wealth / rectification / timing / general` 六类。该层只做路由和审计，不把每个官方方法直接暴露给用户，也不声称已经完成深层语义断语。
- 2026-06-30 轻量映射误判修复：`Dashamamsha` 等分盘名称曾因包含 `dasha` 字符串被误归入 timing。当前已改为按方法词元识别 `Dasa/Dasha` timing 方法，真实轻扫显示 `AllPlanetDashamamshaSign` 归入 `career/marriage/wealth`，不再进入 `timing`。
- 2026-06-30 VedAstro 动态能力选择器结论：系统现在不只知道 641 项目录和主题归类，还会按用户主题生成 `dynamic_selection` 与 `official_report_references`。每个主题会列出自动可用能力、需要额外资料能力、blocked 能力和 `vedastro:<theme>:<method>` 引用 ID，供网页、Skill、MCP 和 Codex prompt pack 指向同一份官方证据层。
- 2026-06-30 报告引用边界：`official_report_references` 是证据引用层，不等于每个引用都已执行成功。`execution_policy != auto` 或 `status != ok` 的能力只能作为“需要补资料/当前阻断”的报告说明，不得包装成已用于最终断语的数据。

## 2026-07-02 解释资料层调用链审计前置结论

- 用户要求在补“调用链显式接入 + 测试”前，先地毯式检查当前项目、历史工作区、技能副本、资料库、Downloads/Desktop 和云端 Git refs，确认是否因不同应用/窗口遗漏资料碎片。
- 当前主仓内已经存在截图所示“行星落十二宫”前端资料层：`jyotish-app/planet-house-details-a.js`、`planet-house-details-b.js`、`planet-house-details-c.js`；与 `.workbuddy/skills/jyotish-vedic-astrology` 旧副本 SHA256 完全一致。
- 当前主仓内已有文章级解释模板注册表：`references/interpretation_template_registry.json`，`scripts/validate_interpretation_templates.py --format json` 返回 `valid=true`、`template_count=11`、`problem_count=0`。
- 当前主仓内已有 P1-P12 与宫位框架资料层：`references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/p1_p12.md` 与 `house_framework.md`；它们包含宫主身份、凶宫主大运禁止美化、Dasha 事件模板、VRY 孤立性、SAV/BAV 交叉等严格解读规则。
- 当前主仓内已有 Raman/BPHS 层：`references/raman-house-judgment-methodology.md`、`references/bphs-ch48-narayana-dasha.md`、`references/yoga_rules.json`、`scripts/validate_bphs_invariants.py`；更完整书籍 PDF 位于资料库路径 `/Users/wuyongnaren/文件仓库/中外🔮占星/国外占星/印度占星书/`。
- `python3 scripts/audit_capabilities.py --mode validate` 通过，显示 `technique_count=89`、`problem_count=0`；`python3 scripts/audit_fragments.py --strict` 通过，显示当前仓 `candidate_count=0`、`untracked_count=0`。
- 云端 HTTPS refs 已确认：本地 `codex/release-hygiene-ci@767a5c6` 与远端 `refs/heads/codex/release-hygiene-ci@767a5c6` 对齐。
- 根因不是“项目没有资料”，而是现有测试多守文档/注册表存在性，没有守 `mcp_server.py::_collect_strict_evidence`、AI prompt pack 和用户可见 strict contract 必须显式携带这些资料层。下一步应只补显式调用链与测试，不重写规则体系。

## 2026-07-02 6月20日后算力消耗升高排查结论

- Codex 本地 `session_index.jsonl` 显示 2026-06-20 开始新增/更新 9 个线程，包括 `开发 flomo App 并上架 App Store`、`优化印度占星项目`、`继续优化星轨talk项目`、`梳理 StarCanvas 进度`、`梳理印度占星项目进度` 等；这不是印度占星单项目单点故障，而是多项目长线程同时启动。
- `.codex/archived_sessions` 中 2026-06-21/22 出现多个 100MB 级长会话：`019eed29...` 约 127MB、`019ee916...` 约 139MB、`019eef04...` 约 58MB。会话统计显示大量 `exec_command` / `apply_patch` / `write_stdin`，并反复产生 `compacted` 记录，说明工具输出和压缩上下文被不断带入模型请求。
- archived session 的 `token_count` 元数据按 last usage 聚合：2026-06-21 约 124.6M total tokens，2026-06-22 约 556.6M，2026-06-23 约 580.5M，2026-06-24 约 366.3M，2026-06-28 约 322.6M。最大线程 `019eed29...` 约 821.6M total tokens，其中大部分为 cached input，但仍会造成显著算力/上下文消耗。
- 直接触发 token 放大的模式是“大范围读取 + 长输出 + 长线程自动压缩”：例如同一回合并行 `sed -n` 读取 README/SKILL/index/API server/多份 reference，每个命令允许 8k-22k 输出 token；后续继续在同一线程中工作，使 cached input 和 compacted 摘要持续变大。
- 代码仓层面，2026-06-21 commit `11bdee3` 把 CI/质量门从轻量 Python 检查升级为安装 Node/npm、`npm ci`、全 pytest、quick quality gate、前端 build、Python package build；后续 `scripts/run_quality_gate.py` 又加入 runtime smoke、browser/release profile、artifact 诊断、manifest gate、oracle gate。这解释了本地/云端 CPU 与 CI 时间增加，但不是模型 token 暴涨的唯一来源。
- 当前本机进程快照显示仍有高负载后台项：Codex app-server 约 60%+ CPU，WorkBuddy renderer/GPU 约 50%/20%+ CPU，一个 Next dev server 占用约 45% CPU 和 27% 内存；这些会造成“电脑算力”体感升高，但和模型 token 账单应分开看。
- `.env.local` 当前开启 `VEDASTRO_ENABLE_NETWORK=1` 且有 endpoint；质量门默认 `skip_vedastro_live=true`，但 strict workflow / VedAstro evidence orchestrator 在真实高严谨工作流中具备出网条件。它是外部 API/网络成本风险点，不是 6月20 起 token 暴涨的主因。
- 根因判断：没有发现占星计算核心的死循环 bug；主要 bug/设计问题是代理工作流缺少“省算力护栏”，包括过宽的文件读取输出、长线程持续携带历史、release/browser gate 被过频触发、多项目 dev server 残留，以及 VedAstro live 配置默认在本地可用时缺少显式预算提示。

## 2026-07-02 省算力开源工具选型与落地

- 全网对比后，最贴合本次根因的直接止血工具是 `squeez`：它是面向 Claude Code、Copilot CLI、OpenCode、Gemini CLI、Codex CLI 的 hook-based token compressor，重点压缩 bash/tool output、代码读取签名和重复上下文，正好对应 6月20 日后“长工具输出 + 长线程压缩摘要膨胀”的问题。
- 已安装并验证 `squeez 1.34.4`，Codex 侧配置位于 `~/.codex/squeez/config.ini`，hooks 位于 `~/.codex/squeez/hooks/`；当前配置 `enabled=true`、`persona=ultra`、`max_lines=120`、`read_max_lines=300`、`grep_max_results=100`、`context_cache_enabled=true`、`redundancy_cache_enabled=true`。
- 已启用 Hermes fallback 插件：`hermes plugins enable squeez-fallback` 返回成功；Codex/Hermes 下一次新 session 或重启后生效。
- `ccusage` 更适合做用量可视化和日/项目维度追踪，已用 `npx --yes ccusage@latest --version` 验证可运行，版本 `20.0.14`；本轮未做全局安装，避免增加长期依赖。
- `Repomix` 适合后续把仓库打包给 AI 前做 token counting 和 include/exclude 控制；它不是本次长线程工具输出膨胀的第一止血点。
- `LiteLLM`、`Langfuse`、`Helicone` 更适合自建 API gateway、OpenAI/VedAstro/多模型调用预算和日志治理；对当前 Codex 本地 agent 会话膨胀不是最短路径，暂不接入。
