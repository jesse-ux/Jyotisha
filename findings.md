# 印度占星产品化发现记录

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
