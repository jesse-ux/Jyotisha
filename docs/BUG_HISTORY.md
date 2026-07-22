# Bug History

本文件是本仓库产品与代码 Bug 的长期知识库。处理任何 Bug 前先读并搜索本文件；完成修复或确认阻塞后，在同一变更中更新本文件。

基础设施、外部引擎、碎片目录和开工预检类风险仍记录在 `docs/research/pre_work_error_ledger.md`。同一问题若同时影响两类台账，应互相引用，不复制大段内容。

## 使用流程

1. 用报错原文、接口路径、状态码、模块名和用户操作搜索本文件。
2. 找到相似记录时，先验证既有防复发措施是否仍存在，再定位新的回归入口。
3. 修复必须包含与风险相称的自动化测试；生产问题还要记录部署版本和脱敏后的生产验证。
4. 完成后更新已有记录，或按下方模板添加新记录。复发问题必须填写 `复发自`，不能伪装成无关的新问题。
5. 不记录姓名、出生资料、邮箱、用户/案例 ID、Cookie、JWT、密码、密钥、完整请求体或模型原文。

## 状态定义

- `investigating`：现象已确认，根因未确认。
- `blocked`：缺少权限、环境或外部条件，当前无法继续验证。
- `mitigated`：用户影响已被安全降级，但根因或全链路尚未闭环。
- `resolved`：根因已修复，并有自动化或真实环境证据。
- `regressed`：历史问题再次出现；必须关联原记录并说明旧防线为何失效。

## 新记录模板

```markdown
## BUG-NNN | 简短标题

- 状态：investigating | blocked | mitigated | resolved | regressed
- 首次发现：YYYY-MM-DD
- 最近更新：YYYY-MM-DD
- 影响面：页面、接口或模块
- 用户现象：脱敏后的可观察现象
- 触发条件：最小复现路径
- 根因：已验证的技术原因；未知时明确写未知
- 修复：实际采取的最小修复
- 验证：测试、生产 smoke、迁移账本或监控证据
- 防复发：测试、约束、监控或发布门禁
- 相关记录：BUG-NNN / ERR-NNN；没有则写无
- 复发自：BUG-NNN；首次出现则写无
- 修复版本：Git SHA、迁移版本或待发布
```

## 已记录问题

## BUG-001 | 对话删除不可用或只改变前端状态

- 状态：resolved
- 首次发现：2026-07-21
- 最近更新：2026-07-21
- 影响面：会话列表、`DELETE /api/sessions/[id]`、Supabase `chat_sessions`
- 用户现象：用户点击删除后对话无法真正删除，或删除交互与账户弹窗不一致。
- 触发条件：登录后删除自己的一条历史会话。
- 根因：删除曾缺少所有者约束的服务端入口和对应数据库授权，前端也没有统一的站内确认面。
- 修复：增加所有者约束的服务端删除接口与数据库 grant，并统一站内确认弹窗。
- 验证：`tests/test_session_management_entrypoints.py`、`frontend/tests/chat-session-delete-contract.test.ts`。
- 防复发：删除必须经服务端所有权校验；测试同时锁定 API、迁移和前端入口。
- 相关记录：无
- 复发自：无
- 修复版本：`e3d619c`、`65b8c42`、`5650ed1`、`fcf5794`

## BUG-002 | Onboarding 首次请求 409、重复请求或读到旧问题

- 状态：resolved
- 首次发现：2026-07-21
- 最近更新：2026-07-21
- 影响面：`POST /api/onboarding`、首页入门问题缓存与恢复
- 用户现象：出生资料已经填写，第一次请求仍返回资料未完成或 `pending`，随后又请求一次并返回缓存结果。
- 触发条件：入门资料完成、缓存生成尚未结束或资料在并发生成期间发生变化。
- 根因：缓存就绪/处理中状态没有完整绑定当前资料指纹，旧请求完成时可能覆盖新资料的生成结果。
- 修复：用全部决策字段生成无明文 SHA-256 身份；领取和完成都使用版本、时间戳和 pending 身份 CAS，并校验账户所有权。
- 验证：onboarding route/cache/candidate completion 测试矩阵，历史完整前端套件 455/455。
- 防复发：缓存命中、pending、超时回收和完成写入必须绑定同一资料身份；任何旧请求只能返回安全 `pending`。
- 相关记录：无
- 复发自：无
- 修复版本：`28d58d4`、`5ee925c`、`308e5d5`、`e13d595`、`346ec02`、`a9ffbd9`

## BUG-003 | 浏览器原始报错 “The string did not match the expected pattern” 泄露给用户

- 状态：resolved
- 首次发现：2026-07-21
- 最近更新：2026-07-21
- 影响面：生时校正自动流程、候选时间确认、“都不符合”分支
- 用户现象：选择候选时间或“都不符合”后直接看到浏览器英文 DOMException。
- 触发条件：自动或手动生时流程中的底层浏览器/传输异常进入未归一化错误分支。
- 根因：部分 journey effect 直接展示实现层异常信息，没有统一转换为安全、可操作的中文错误。
- 修复：所有相关 mutation/effect 统一经 `birthTimeUserError` 归一化，屏蔽 DOMException、网络和语法实现细节。
- 验证：`frontend/tests/birth-time-user-errors.test.ts` 包含该英文原文回归用例。
- 防复发：禁止 `setError(caught.message)`；新增异步入口必须走统一错误映射。
- 相关记录：无
- 复发自：无
- 修复版本：`a38a096`

## BUG-004 | 点击生时校正后先进入中间卡片，失败时无法自然回到首页

- 状态：resolved
- 首次发现：2026-07-21
- 最近更新：2026-07-22
- 影响面：首页生时校正入口、首轮加载与恢复 UI
- 用户现象：点击入口后先看到“开始生时校正”或“正在恢复账户里的校正进度”卡片；依赖失败时停留在重试卡片。
- 触发条件：首轮校时 RPC 尚未返回或返回失败。
- 根因：页面在首轮有效 turn 生成前就切换到专用校正会话。
- 修复：首轮生成期间保持首页；只有有效首轮 turn 返回后才进入校正会话，失败以首页输入区提示呈现。
- 验证：`frontend/tests/consultation-entrypoint.test.ts` 及生产入口 smoke。
- 防复发：会话切换以“首轮可展示结果”而非“请求已发出”为边界。
- 相关记录：ERR-087
- 复发自：无
- 修复版本：`dc0077e`

## BUG-005 | 保存出生时间返回 `PATCH /api/account` 500

- 状态：resolved
- 首次发现：2026-07-21
- 最近更新：2026-07-22
- 影响面：账户出生资料、Supabase `profiles`
- 用户现象：选择记录时间和误差后显示“暂时无法保存账户资料”，接口返回 500。
- 触发条件：账户已被候选时间写入 reported 字段，之后再次编辑原始出生时间声明。
- 根因：旧触发器把候选/活动时间复制为用户报告时间，同时数据库又把报告时间视为不可变字段。
- 修复：报告时间保持可编辑，禁止候选时间反写原始声明，修复不一致历史行并增加来源/时间一致性约束。
- 验证：迁移 `20260721140000` 已进入生产账本；生产合成账户修改与恢复均返回 200。
- 防复发：候选、活动、用户报告时间保持独立语义；profile persistence 测试锁定迁移行为。
- 相关记录：ERR-088
- 复发自：无
- 修复版本：`dc0077e`、`20260721140000_repair_reported_birth_time_revision.sql`

## BUG-006 | 生时校正首轮在没有历史事件时进入确认态并返回 409

- 状态：resolved
- 首次发现：2026-07-21
- 最近更新：2026-07-22
- 影响面：`POST /api/birth-time-conversation` 首轮、计费释放
- 用户现象：等待约一至两分钟后首轮返回 `action_conflict`，费用预留被释放。
- 触发条件：技术扫描在零条历史事件时直接返回 `ready_for_confirmation`。
- 根因：应用构建了 `confirming` 首轮，而数据库契约只允许首轮为 `active`；技术就绪错误绕过了三条有效历史事件的业务门槛。
- 修复：所有技术包统一经过 `MINIMUM_SCOREABLE_EVENTS` 门禁；未满三条时清除 result ID，并保持 `pending_validation/active`。
- 验证：核心 orchestrator/e2e 回归测试；生产首轮随后成功创建并收费一次。
- 防复发：确认态只能由三条以上有效、已发生、可评分事件触发。
- 相关记录：ERR-089
- 复发自：无
- 修复版本：`b8ed740`

## BUG-007 | `finance` 证据通过应用校验但被数据库拒绝为 409

- 状态：resolved
- 首次发现：2026-07-21
- 最近更新：2026-07-22
- 影响面：生时校正技术包、事件证据、Supabase durable validators
- 用户现象：真实首轮计算完成后仍返回统一的 `action_conflict`。
- 触发条件：D2/D11 产生 `finance` 建议主题，或摘要包含应用已支持的 `domain` 字段。
- 根因：TypeScript 已支持 `finance` 和摘要 `domain`，初始 SQL 枚举及表约束仍是旧版本。
- 修复：向前迁移同步 evidence request、life event、private candidate、public recap 和事件表约束。
- 验证：迁移 `20260721150000` 已进入生产账本；迁移契约测试和生产首轮 smoke 通过。
- 防复发：应用证据枚举变更必须同时更新 durable SQL，并由迁移契约测试检查。
- 相关记录：BUG-006、ERR-090
- 复发自：无
- 修复版本：`b981c4e`、`20260721150000_align_conversational_finance_domain.sql`

## BUG-008 | 后续证据把范围压得过窄后返回 503

- 状态：resolved
- 首次发现：2026-07-21
- 最近更新：2026-07-22
- 影响面：生时校正后续回答、技术包构建
- 用户现象：首轮、“都不符合”、暂停恢复均正常，但提交后续明确事件时返回 `service_unavailable`。
- 触发条件：事件评分产生的窄区间不足两个时间样本或不足两个可区分分盘主题。
- 根因：这是“证据仍不足”的正常业务状态，代码却把它作为 `TypeError` 依赖故障终止。
- 修复：显式分类区间区分度不足；撤回本次过度收窄，保留上一候选范围、评分证据和未确认状态，然后继续提问或安全保存范围。
- 验证：核心回归 85/85；生产从失败点续跑通过；全新生产 smoke 覆盖资料、首轮、“都不符合”、暂停恢复、多事件、范围终态、计费和问题交接。
- 防复发：任何新候选范围必须先满足技术证据契约；不满足时回退，不返回 503，也不伪造确定分钟。
- 相关记录：ERR-091
- 复发自：无
- 修复版本：`b981c4e`

## BUG-009 | 未校正的已填报时间被降级为零星盘咨询

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：生日初始化、普通咨询路由、生时校正提示
- 用户现象：已填写具体出生时间但没有完成生时校正时，普通问题仍提示只能回答一般知识或必须先完成校正。
- 触发条件：出生时间来源包含有效具体分钟，但状态不是 `confirmed`，且当前聊天没有旧的临时授权状态。
- 根因：前端把“使用未校正填报时间”设计成逐会话授权；没有授权时默认退回 `general_no_birth_time`，因此完全绕过现有的未校正星盘安全模式。
- 修复：具体填报时间现在自动进入 `unverified_birth_time`，保留禁止精确应期的安全边界但不禁用个人分析；无具体分钟时直接进入无分钟模式；移除校正 toast、弹窗和每条回答前重复的校正警告，并把生日入口收敛为“知道准确时间 / 不确定准确时间”两个选择。
- 验证：`frontend/tests/birth-time-consultation-consent.test.ts`、`frontend/tests/consultation-entrypoint.test.ts`、`frontend/tests/consultation-birth-time-mode.test.ts`、`frontend/tests/birth-time-intake.test.ts`。
- 防复发：咨询路由测试锁定“有效填报分钟无需授权即可使用”；页面契约禁止重新引入生时校正 toast 或阻断式选择。
- 相关记录：BUG-003、BUG-004
- 复发自：无
- 修复版本：待提交（本地可测）

## BUG-010 | 浏览器直连 Supabase 写会话泄露 `TypeError: Load failed`

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：回答完成后的聊天记录持久化、移动 Safari 错误提示
- 用户现象：回答已经生成，但页面反复显示“云端同步失败：TypeError: Load failed”，并要求复制保存后重试。
- 触发条件：浏览器直接向 Supabase `chat_sessions` 发起跨域写入时发生传输失败。
- 根因：会话读取和多数业务写入已经使用同源 Next.js API，但会话创建与更新仍由浏览器客户端直写 Supabase；异常原文又被拼进回答错误区域。
- 修复：新增同源 `POST /api/sessions` 与 `PATCH /api/sessions/[id]`，服务端校验登录、所有权和写入负载；客户端对可重试失败短重试一次，并把最终失败降级为输入区状态提示，不再把浏览器异常原文渲染成回答错误。
- 验证：`frontend/tests/chat-session-write.test.ts` 覆盖同源路由、所有者约束、短重试和 `Load failed` 脱敏；相关咨询与资料回归测试通过。
- 防复发：会话写入契约禁止页面直接调用 `supabase.from("chat_sessions")`；网络异常必须映射为稳定用户文案。
- 相关记录：BUG-001、BUG-003
- 复发自：无
- 修复版本：待提交（本地可测）

## BUG-011 | 对话消息暴露内部证据审计状态

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：普通问答消息、Agent 回答顶部区域
- 用户现象：回答正文上方显示“证据状态：not-applicable”和“证据链摘要 · not-applicable”等工程审计信息，正文下方还显示单条回答的报告下载控件。
- 触发条件：任意已完成的 Agent 回答，尤其是后端返回 `not-applicable` 时。
- 根因：消息行对每条非思考态 Agent 消息无条件渲染 claim boundary 与 Technique Audit Table；未识别状态又直接回退显示原始状态值。
- 修复：从普通聊天消息行移除内部证据徽章、审计面板和单条回答报告下载控件；证据状态和 workflow receipt 仍随消息保存并供内部约束使用。
- 验证：`frontend/tests/claim-boundary-badge.test.ts`、`frontend/tests/evidence-audit-panel.test.ts`、`frontend/tests/consultation-report-export.test.ts` 锁定聊天消息不再挂载这些内部组件。
- 防复发：聊天消息渲染契约禁止直接展示 `techniqueTruth` 和 `workflowReceipt`；需要运营或调试时使用独立的受控界面。
- 相关记录：BUG-009
- 复发自：无
- 修复版本：待提交（本地可测）

## BUG-012 | 自动生时流程重构后再次直出实现层错误

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：生时校正自动出题与评分轮询、`use-birth-time-automatic-journey-effects`
- 用户现象：自动流程失败时可能再次显示底层异常原文，而不是稳定、可操作的中文提示。
- 触发条件：自动出题或评分轮询 Promise 进入异常分支。
- 根因：出生时间流程重构保留了 automatic effect 中直接读取 `caught.message` 的旧分支；原回归测试后来只检查 guided hook，因此没有锁定 automatic hook 的两个入口。
- 修复：automatic effect 的出题与轮询异常统一经过 `birthTimeUserError`；回归测试同时检查 guided 与 automatic 两个 hook，并禁止两种直接展示 `caught.message` 的写法。
- 验证：`frontend/tests/birth-time-user-errors.test.ts`。
- 防复发：错误归一化测试按入口文件验证安全不变量，不再依赖单文件精确调用次数。
- 相关记录：BUG-003
- 复发自：BUG-003
- 修复版本：待提交（PR #25）

## BUG-013 | 精简生时校正文案后真实 Chromium 测试等待已删除标题

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：`frontend/tests/conversational-rectification-component.test.ts`、前端完整质量门禁
- 用户现象：页面已经正确渲染候选时间、经历和输入控件，但测试持续等待并最终报 `Timed out waiting for async initial turn`。
- 触发条件：运行真实 Chromium 390px 组件回归测试，并把 active turn 注入精简后的生时校正界面。
- 根因：产品把重复的“当前判断”叙事改成“已记录”行动文案后，浏览器测试仍以旧标题作为异步渲染完成信号。
- 修复：测试改为等待候选代表时间与已记录经历两个稳定结构信号，不再绑定可变标题文案。
- 验证：`frontend/tests/conversational-rectification-component.test.ts`。
- 防复发：真实浏览器等待条件优先绑定语义结构和状态数据，不用已批准可调整的展示标题充当加载边界。
- 相关记录：BUG-004
- 复发自：无
- 修复版本：待提交（PR #25）

## BUG-014 | 能力审计新增案例验证主题后质量门禁仍断言旧主题集合

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：`tests/test_api_server_security.py`、Python quick quality gate
- 用户现象：能力审计正确返回 `Case Validation` 并将案例验证评为可产品化，但质量门禁仍按旧主题集合和 `thin` 等级失败。
- 触发条件：运行能力审计测试，且应用可见主题已包含案例验证入口。
- 根因：案例验证能力进入 `_app_visible_topics` 后，对应主题集合和 UX 等级断言都没有同步更新。
- 修复：把 `Case Validation` 纳入预期可见主题，并把 `case_validator` 从 `thin` 队列移入 `excellent` 断言，保持测试与同一审计规则一致。
- 验证：`tests/test_api_server_security.py::test_capability_audit_scans_registry_and_local_sources`；Python quick quality gate。
- 防复发：扩展应用可见主题时必须同时更新能力审计契约测试；精确集合断言继续用于发现意外增删。
- 相关记录：无
- 复发自：无
- 修复版本：待提交（PR #25）

## BUG-015 | 分钟校正 safeguards PR 与主线证据契约分叉

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：分钟候选输入身份、公共 holdout 校验、三引擎证据包、PR quality gate
- 用户现象：PR 与 `main` 在五个文件发生冲突，聚焦测试通过但完整 quick quality gate 在 API 安全测试收集阶段失败。
- 触发条件：基于旧基线开发 v1 holdout safeguards，同时主线独立升级到 v2/v3 证据契约并移除旧 API store 导入。
- 根因：PR 复用了旧 holdout 字段和 `true node` 默认，未执行与 CI 相同的 quick quality gate；主线已经采用 `mean node` 和更严格的 sealed holdout schema。
- 修复：以主线为准新增兼容的输入指纹、邻近分钟探针和语义哈希；新增 v4 独立审核、日级事件、假分钟承诺门禁及非生产 intake；不恢复旧自动评估循环。
- 验证：分钟校正聚焦回归、脚本直接执行检查、Ruff、Python compilation 和 quick quality gate。
- 防复发：新 safeguards 必须以当前 schema 向前升级；候选身份必须继承产品计算默认；PR 验收必须包含 workflow 实际执行的 quick quality gate。
- 相关记录：BUG-009、BUG-014、ERR-045、ERR-053、ERR-086
- 复发自：无
- 修复版本：d7d9703

## BUG-016 | 生时校正首轮被扫描稀疏度或候选分区超时打成 503

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：首页“先完成生时校正”、`POST /api/birth-time-conversation` 首轮技术包
- 用户现象：点击生时校正后仍停留在普通咨询页，并显示“生时校正暂时无法继续”；接口返回 503。
- 触发条件：候选扫描包含真实但不连续的时点差异，或动态候选分区依赖在 45 秒内没有返回。
- 根因：技术包只承认相邻分钟切换，错误拒绝了稀疏扫描中的真实范围差异；同时首轮把用于改善问题排序的候选分区依赖当成不可降级的硬依赖。生产版本 `b981c4e` 的日志分别记录了 `RectificationTechnicalPacketRangeError` 和 `candidate_differences TimeoutError`。
- 修复：稀疏扫描差异改用明确的范围级文案，禁止伪称相邻分钟切换；超过六小时的宽范围首轮跳过分钟级候选分区，较窄范围在候选分区发生已知超时、取消、配置或服务故障时保留服务端扫描证据并继续收集，不再返回 503；未知编程或契约错误仍失败关闭。
- 验证：`frontend/tests/conversational-technical-packet.test.ts`、`frontend/tests/conversational-rectification-route.test.ts`、真实 Chromium 390px 组件回归和 `npm run build` 通过；完整前端套件 844 项中 837 项通过，余下 7 项均为沙箱 Chromium / PostgreSQL 端口环境失败，针对性 Chromium 在沙箱外 8/8 通过。
- 防复发：首轮必须区分核心扫描失败与可降级的候选排序依赖；稀疏差异文案必须显式否认相邻分钟切换；生产验收必须核对接口状态与实际进入校正会话。
- 相关记录：BUG-004、BUG-008、ERR-091
- 复发自：无
- 修复版本：待提交（本地可测）

## BUG-017 | 候选范围终态继续原问题必定返回 409

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：生时校正范围终态、`POST /api/consult`、durable 原问题交接
- 用户现象：生时校正安全结束并保存候选范围后，点击“继续原问题”仍提示原问题状态变化，接口返回 409。
- 触发条件：分钟确认发布门禁未通过，校正以 `candidate.status=pending_validation` 完成；页面按未确认分钟选择 `unverified_birth_time` 并携带 durable handoff。
- 根因：页面正确区分确认分钟与保存范围，但咨询接口把所有 handoff 硬限制为 `verified_chart`；范围终态因此在计费和模型调用前被拒绝。
- 修复：handoff 允许 `verified_chart` 与 `unverified_birth_time` 两种星盘模式，继续拒绝 `general_no_birth_time`、旧校正入口和不一致 request ID；分钟确认门禁保持不变。
- 验证：生产合成账号复现 `409 mode_changed`；`frontend/tests/consultation-birth-time-mode.test.ts` 锁定范围终态模式与一般咨询隔离；发布后需复跑 durable claim、正常咨询和聊天删除 smoke。
- 防复发：范围终态和精确确认必须分别覆盖 continuation 模式；不得把“拥有 handoff”错误等同于“已经确认出生分钟”。
- 相关记录：BUG-008、BUG-009、BUG-016、ERR-085、ERR-091
- 复发自：无
- 修复版本：待提交（生产 smoke 待当前精确 SHA 发布后补齐）
