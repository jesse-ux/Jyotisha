# 印度占星 Web/App 产品化任务计划

目标：把当前印度占星网页/app推进到同品类成熟产品水平，持续对标开源项目与本地碎片，优先复用 MIT/Apache 代码或现有本地模块，避免重复造轮子。

## 当前阶段

- 状态：in_progress
- 阶段：用户端信任层与运行可用性
- 本轮最高优先级：在已完成首次使用引导、真实浏览器首跑冒烟、AI/API key 安全提示、导出失败恢复后，推进星历后端抽象可行性，把 SwissEph/WASM/xalen/VedAstro/PyJHora 的替换边界变成可检测资产。

## 执行原则

1. 每次实现前先扫描本地碎片、`references/open_source_sources/*`、现有测试与产品差距矩阵。
2. 网络可用时先查 GitHub/开源项目；许可证允许且架构贴合时优先复用。
3. 不直接复制 AGPL/GPL 代码；只作为行为基准或独立重写参考。
4. 每完成一个任务，立刻分析下一个最高优先级问题并继续执行。

## 已完成

- [x] 可见参数/日历/工作区面板。
- [x] HTML 报告导出基础版。
- [x] Panchanga range API、月历、CSV/ICS、Rahu Kala/Yamaganda/Gulika。
- [x] Choghadiya、Hora、Tithi/Nakshatra/Yoga end times。
- [x] 保存星盘工作区：保存、打开、删除、导出、ID 修复。
- [x] Synastry 保存伴侣、保存配对、重新打开/删除、JSON 导出、HTML 报告导出。

## 进行中

- [x] Panchanga richer vrata/festival candidate rules。
- [x] Panchanga search-by-condition 条件检索。
- [x] CSV/ICS/前端表格/月历同步暴露条件标签。
- [x] 构建与碎片审计。
- [x] 多人/家庭分组与更强案例过滤。
- [x] 关系报告模板与比较视图。

## 下一批优先级

- [x] 多人/家庭分组。
- [x] 关系报告模板。
- [x] bi-wheel/composite-style 比较视图。
- [x] `spouse_status_yoga.py` 关系深度折叠。
- [x] 关系报告打印/PDF polish。
- [x] 可编辑关系元数据。
- [x] 后端 PDF 管线。
- [x] 更深关系时机/UL/DK 折叠。
- [x] Panchanga 搜索增强：组合条件、节日说明、location-aware 日历默认值。
- [x] 专业报告后端 PDF 管线：复用 `report_builder.py` 生成后端 HTML/PDF artifact。
- [x] 计算设置选择器：ayanamsa/node/house/sunrise/geocoder policy。
- [x] 规则/技法检索目录与 API explorer。
- [x] 规则变体/流派结果口径：Yoga/Ashtakavarga/Shadbala API 返回 `rule_variants`，Skill workbench 渲染规则口径。
- [x] 候选碎片接入：`curse_yoga_detector.py` 已进入 `/api/yogas`，`shadbala_advanced.py` 已进入 `/api/shadbala` 增强证据层。
- [x] 候选碎片接入：`dasha_analyzer.py` 已进入 `/api/dasha.vimshottari_analysis` 与主 Dasha 详情卡。
- [x] 候选碎片归档：`reading_orchestrator.py`、`report_orchestrator.py`、`orchestrator_bridge.py` 已由 `/api/thematic_report`、registry 与前端 Skill workbench/API Explorer 引用，不再是漂浮碎片。
- [x] 候选碎片接入：`mevg_automation.py` 已进入 `/api/case_validation.mevg_gate`，只读门控状态，不运行子进程。
- [x] 候选碎片归档：`hermes_bridge.py` 判定为外部个人 agent/WorkBuddy 学习桥，写入 `~/.workbuddy`，不属于印度占星网页/app 默认产品面，已加入碎片审计忽略。
- [x] 主题报告真实证据链：`/api/thematic_report` 在传入出生数据或星盘数据时自动派生 chart/dasha/yogas/shadbala/ashtakavarga/relationship/career/Jaimini 证据，前端显示 evidence source 与模块状态，不再把样例报告伪装成实算报告。
- [x] 方法文档与 API 示例：Technique Directory/API Explorer 已返回并展示可复制 cURL、最小 OpenAPI 片段、方法摘要、边界说明和 API doc key。
- [x] PWA/信任中心 MVP：manifest、service worker、installability 状态、Trust Center 本地数据说明、导出本地资料、二次确认清空本地资料。
- [x] 术语模式与星历底座记录：Calculation Settings/Trust Center 支持 balanced/beginner/professional，tooltip、provenance、JSON/HTML 导出记录术语模式和 ephemerisBackend，xalen-ephemeris 作为 Apache-2.0 可行性记录。
- [x] 桌面/普通用户运行健康检查入口：Trust Center 接入 `/api/health`、`/api/capability_audit`、PWA 状态和桌面路线提示，普通用户可直接检查本地 API 与能力目录是否可用。
- [x] 剩余同品类产品 polish：首次使用引导与普通用户空状态路径已提供运行健康检查、示例盘填入、导入聚焦和本地星盘库空状态指引，降低首次运行/无星盘/无 API 时的卡点。
- [x] 浏览器首跑守门：已用真实 Chrome 检查首屏首次使用路径、移动端布局、示例盘生成、运行健康检查入口，并修复 API 字段缺失导致的 Banner `undefined`。
- [x] AI/API key 安全提示：AI 聊天不再提示浏览器 localStorage endpoint 配置；改为提示通过服务端 `/api/chat` 或后端代理读取服务端 `OPENAI_API_KEY`。
- [x] 导出失败恢复：PDF fallback 和导出异常会提示 HTML 降级、Trust Center 健康检查和本地 API 启动命令。
- [x] Ephemeris abstraction feasibility：新增 `scripts/ephemeris_backend_probe.py` 和研究记录，明确 `swisseph_python` 主路径、`swisseph_wasm` fallback、`xalen_ephemeris` spike、`vedastro` product/API benchmark、`pyjhora_benchmark` AGPL benchmark-only。
- [x] Ephemeris adapter contract：新增 `scripts/ephemeris_adapter_contract.py` 与 parity matrix 文档，固定 Sun/Moon/Asc/Rahu/Ketu 的 `longitude_delta_arcsec` 验收口径。
- [x] Runtime smoke 补强：`tests/run_frontend_runtime_smoke.py` 现在真实检查 `/api/report_artifact` HTML fallback 和 `AI_BROWSER_KEY_DISABLED` 前端密钥禁用策略。
- [x] Ephemeris candidate adapter spike：新增 `scripts/ephemeris_candidate_adapter_spike.py` 与研究文档，记录 `swisseph_wasm_candidate`、`xalen_ephemeris_candidate` 的 license gate、parity gate 和 runtime setting 暂不开放。
- [x] 登录/订阅/API 失败恢复提示：`auth.js` 安全解析非 JSON 响应，登录/注册/Apple/token 校验失败会提示 Trust Center、`npm run web`、`python3 scripts/jyotish_api_server.py`；`subscription.js` 用可关闭通知替代关键 IAP alert，并转义错误消息。
- [x] 主排盘/关系/问事/Transit/API bridge/AI chat 失败恢复提示：安全解析非 JSON 响应，普通用户可见 Trust Center、`npm run web`、`python3 scripts/jyotish_api_server.py` 恢复路径，不再只弹 alert 或显示裸错误。
- [x] 真实浏览器点击级 smoke：新增 `tests/run_frontend_click_smoke.py`，覆盖示例盘生成、AI chat、HTML 导出、Transit、合盘、问事；修复 HTML 导出链路中的 `sub_lord` ReferenceError。
- [x] 移动端/离线/PWA 点击守门：`tests/run_frontend_click_smoke.py --mode all` 覆盖在线桌面、移动首屏、manifest/serviceWorker、无 API 健康检查和排盘 fallback，并纳入 `scripts/run_quality_gate.py` 默认质量门。
- [x] 桌面应用/安装后首次打开路线：`scripts/desktop_packaging_preflight.py` 输出 PWA installed shell、Pake first launch、Tauri sidecar readiness 三类 first-launch checks；README 与 desktop packaging spike 同步可执行命令。
- [x] Pake/Tauri 本机可用性探测：`scripts/desktop_packaging_preflight.py` 新增 `toolchain_probe`，只读检查 node/npm/rustc/cargo/xcodebuild/pake/tauri，明确 Pake GPL-3.0、Tauri sidecar/signing_notarization 边界，不生成真实包。
- [x] PDF fallback / PWA 离线 shell / 移动长标签点击守门：`tests/run_frontend_click_smoke.py --mode all` 真实点击 PDF fallback、service worker 离线二次加载、移动端 Complete/Vargas/Synastry/Prashna/Transit Compare 标签切换，并修复 service worker 把 HTML fallback 返回给 JS module 请求的 MIME 噪声。
- [x] 报告/导出后端 artifact 用户可见完整性：`/api/report_artifact` 返回 `artifact_status`、`primary_artifact`、`download_filename`、`download_mime`、`fallback_reason`、`user_message`、`next_action` 与 `delivery` 镜像；前端 PDF 下载优先使用后端下载契约，runtime smoke 验证 HTML artifact 状态和文件名。
- [x] 真实浏览器导入/案例库工作流守门：`tests/run_frontend_click_smoke.py --mode workspace` 覆盖文本星盘识别、填表生成星盘、保存本地星盘、重新打开、参数/日历工作区保存、导出已选案例和导出整库，并已纳入 `--mode all`。
- [x] 移动端导出菜单与 Trust Center 长内容：390px 视口下导出菜单不遮挡、长面板无横向溢出，健康检查/本地数据/安装说明在移动端可读可操作。
- [x] 真实浏览器点击级 smoke 命令级超时/残留进程诊断：`--timeout`、process snapshot、日志尾部与强制清理已进入脚本，长链路异常时不再静默挂起或遗留 API/Vite 子进程。
- [x] 普通用户长链路质量门失败摘要：`scripts/run_quality_gate.py` 输出可行动失败摘要、cwd、stdout/stderr 尾部、click smoke reason/process_snapshot，并修复前端构建 cwd 指向 `jyotish-app`。
- [x] PDF/文本星盘导入文件上传真实浏览器守门：`tests/run_frontend_click_smoke.py --mode import-files` 覆盖文本文件上传解析、PDF 文本抽取失败恢复、导入后字段质量提示与移动端文件选择入口，并纳入 `--mode all`。
- [x] 普通用户安装/启动文档与质量门输出统一：README 增加“普通用户启动路径”，质量门失败摘要输出同一套网页/API/Trust Center 步骤，明确 PWA 只包装网页壳、本地 API 仍需单独启动。
- [x] README/应用内 Trust Center/失败恢复文案术语一致性：应用界面统一使用“普通用户启动路径 / 网页服务 / 本地 API 服务 / PWA 安装壳”，命令只保留在 README 与质量门失败摘要里。
- [x] 质量门分层与运行成本：`scripts/run_quality_gate.py --profile quick|browser|release` 已拆分快速开发守门、完整浏览器守门、发布前守门，并保留 `--frontend-click-mode` 作为局部浏览器路径复验入口。
- [ ] 整机与 Git 云端地毯式遗漏审计：只读枚举整机印度占星相关资料、历史工作区、技能包、引擎碎片、git 仓库与当前远端所有 refs；把遗漏能力/代码/资料反向映射到当前网页/app。
- [x] 整机与 Git 云端地毯式遗漏审计第一轮：已完成高相关目录、历史报告、云端 HTTPS mirror、远端 refs、关键词覆盖矩阵与遗漏优先级文档。
- [x] Ashtakavarga Prashtara / Yoga Pinda 第一类产品化闭环：复用现有 `calc_prastara_av`，新增 `calc_yoga_pinda` 一等契约，并补 API、前端 Skill workbench、registry 与测试守门。
- [x] Sripathi/Placidus 房宫算法用户可控切换与 parity 守门：Bhava Chalit 读取 Calculation Settings 的 `houseSystem`，API 返回 requested/selected/available house systems、Placidus 所需 birth JD/location 与 fallback 元数据，前端工作台显示宫位制、可选系统、宫位边界与迁移摘要。
- [x] KP Horary 产品化闭环：Prashna API 返回 `kp_horary`，包含可选 1-249 `horary_number`、ruling planets、cuspal sub-lord、house significators 与 judgement matrix；前端 Prashna 结果和案例保存/导出保留该证据。
- [x] Tajika Harsha/Panchavargiya Bala 产品化闭环：`scripts/tajika.py` 新增 Harsha/Panchavargiya/综合强度层，`solar_return.py` 与 `varshaphala.py` 年报均返回 `tajika_strength`，Skill Workbench 显示年度强度与风险摘要。
- [x] Muhurta date-range solver：`scripts/muhurta.py` 新增 `muhurta_range_search`，`/api/muhurta` 支持 `start_date/end_date/activity/limit/location` 范围搜索，Skill Workbench 展示候选日期、推荐窗口和过滤原因。
- [x] Sayanadi/Shayanadi Avastha 与 D24/D30/D60 深度模板产品化：新增 `/api/deep_varga_avastha` 聚合层，复用 `avastha_calculator.py`、`divisional_charts_extended.py`、`trimshamsa_d30.py`，Skill Workbench 展示 Avastha 主导状态、深分盘模板与风险标记。
- [x] 二轮整机/Git/开源对标审计与全球排名更新：注册表 68 技法、37 API、碎片审计 0 问题；补齐 `deep_varga_avastha` 注册表/目录/审计映射，确认第一类产品化缺口已闭环。
- [x] 发布/仓库卫生第一步：release profile 新增关键产品文件未跟踪守门，28 个产品关键 untracked 文件已纳入 Git 暂存，`audit_fragments.py --strict` 当前报告 untracked_count=0。
- [x] 完整 browser/release profile 与云端分支同步检查：browser/release profile 均通过，分支 `codex/release-hygiene-ci` 已推送到远端并更新现有 PR #6。
- [x] PR CI 云端稳定性修复：`.github/workflows/ci.yml` 显式使用 `--profile quick --skip-yoga-logic`，避免 PR 环境因未安装真实浏览器/Playwright 依赖而误触 browser click smoke。
- [x] GitHub Actions 失败根因修复：本地复现 PR `validate` 的 Ruff E402 与 `test` 全量 pytest 的 WorkBuddy 旧 skill 路径污染，新增 pytest import guard 并修复 Ashtakavarga lint。
- [x] Clean checkout CI 复现与修复：用干净 clone 复现 `.git/lost-found` 本机残留假设和 KP 外部 CSV fixture 缺失，修复为 clean checkout 可运行/可跳过的测试策略。
- [x] 发布包基础链路验证：wheel/sdist 构建成功，`twine check dist/*` 通过，全新 venv 安装 wheel 后 CLI help 可用。
- [x] PR merge ref 复现与 release-only workflow 守门：在 `/tmp/yinduzhanxing-pr6-merge` 拉取 PR #6 merge ref，确认完整依赖安装后 pytest 与 quick gate 通过；新增手动发布质量门 workflow 跑 release profile 与 Playwright Chromium，并为 CI/test workflow 增加 Vite/Node/Python 诊断。
- [x] CI 失败 artifact 诊断：pytest 改为 `-vv --maxfail=1 --junitxml`，quick/release quality gate 输出 tee 到 artifact，避免云端只暴露 exit code。
- [x] 云端 CI 收口：PR #6 head `925e73e` 的 `validate`、`test`、`release-quality-gate` 三条 GitHub Actions 检查均已通过。
- [x] 准确率透明度页面：Trust Center 新增 Validation Transparency 面板，展示 Yoga logic benchmark 的 60 charts、82 comparable rules、Precision/Recall/F1、unmapped_pyjhora 与“不是个人事件预测准确率”的边界说明。
- [x] 普通用户交付形态：新增 deployment preflight 与 README 交付矩阵，明确 Local dev、Docker Compose、Static demo/PWA、Desktop shell 的入口、命令和 API 边界，并纳入 quick/release 守门。
- [x] Antigravity/VedAstro 外部评审复核：确认 D1/D9 对齐，纠正 Shadbala/秒级输入过期结论，新增 Dasha 参考差异审计记录。
- [x] Level 3 外部解盘审计：拆分可采纳解读与可计算错误，并修复 D1 尊严状态漏掉友敌标签的问题。
- [x] Skill 分发同步：根 `SKILL.md` 已修正 Shadbala/对标边界，`skills/jyotish-engine-modules` 的分盘脚本副本已同步 D81/D108/D144 归一化修复，并新增守门测试防止 skill 与网页/app 主线再次漂移。
- [x] 公开演示环境 polish：首屏与 Trust Center 新增静态 demo/PWA 无 API 能力边界，README 与 `deployment_preflight.py` 增加 `static_demo_boundary_visible` 守门，明确 Vercel/Netlify/GitHub Pages 只适合作为静态壳，完整技法走 Docker Compose 或本地双服务。
- [x] Dasha/Shadbala 外部 oracle 边界第一步：新增 `references/oracle/dasha_shadbala_oracle_cases.json` 与 `scripts/oracle_boundary_audit.py`，把用户 PDF 的 Vimshottari 起点差异和 Shadbala 分量级校准缺口纳入可重复审计报告。
- [x] VedAstro 黄经 oracle 接入：`longitude_cases` 已记录用户盘 9 项外部 sidereal longitude，本地最大差约 26.23 角秒且 D1/D9 落点一致；该样本只用于 ephemeris drift 审计，不作为 Dasha/Shadbala 调参依据。
- [x] Multi-Ayanamsa 计算层可验证切换：`full-reading --ayanamsa` 已在输出中记录 `ayanamsa_name/display/value`，`compute_chart_data(..., ayanamsa_name=...)` 也能直接切换；测试覆盖 Lahiri/Raman/KP 差异。
- [x] AI Native Prompt/RAG 承载层第一步：`full-reading.ai_prompt_pack` 输出证据快照、检索文档、边界约束和结构化中文提示词，供网页/app 或 skill 后端 AI 代理生成高阶解读。
- [x] Antigravity AI 副手工作单：新增 `docs/research/antigravity_sidecar_work_order_2026_06_25.md`，把 Antigravity 限定为外部 oracle 样本采集、网页/app 审计、skill 同步审计和浏览器用户流验证，避免与核心计算修改冲突。
- [x] Standalone ayanamsa 全局状态修复：新增 `scripts/ayanamsa_utils.py`，让 Transit、Solar Return、Muhurta、cmd_muhurta、Yoga 验证脚本在 `FLG_SIDEREAL` 前显式设置 ayanamsa；默认 Lahiri，调用方可显式传入 Raman/KP 等。
- [ ] 下一步：继续扩充多来源 oracle 样本，补 JHora/PyJHora 的 Moon sidereal longitude、ayanamsa、Vimshottari 起点和 Shadbala 六分量目标值；同时把前端 Multi-Ayanamsa 设置与 `ai_prompt_pack` 可视化。
