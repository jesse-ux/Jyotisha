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

## BUG-018 | 首次保存未确认出生时间没有写入档案状态

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：账户出生资料保存、未确认星盘咨询、生时校正后继续原问题
- 用户现象：已经保存“大概时间”等出生资料，但继续咨询时仍提示出生时间状态发生变化，接口返回 409。
- 触发条件：档案没有旧的 active minute、legacy minute、candidate 或 case pointer，第一次经账户接口保存未确认出生时间声明。
- 根因：账户写入只在清除旧候选结果时补写 `birth_time_status=reported`；干净档案和首次 upsert 被提前跳过，留下完整声明但空状态，随后被服务端星盘真值校验拒绝。
- 修复：所有未确认声明变更都原子写入 `reported` 并清空不可沿用的应用结果；首次创建档案时也写入同一状态；确认分钟仍禁止被普通资料编辑覆盖。
- 验证：`frontend/tests/account-api.test.ts` 覆盖空状态档案与首次档案写入；生产使用认证账户重新保存合法声明后复跑范围终态 handoff、模型咨询、计费和会话删除。
- 防复发：出生声明与 `birth_time_status` 必须由同一次服务端写入建立，不允许依赖后续校正流程补齐状态。
- 相关记录：BUG-009、BUG-017
- 复发自：无
- 修复版本：待提交

## BUG-019 | 原问题交接租约过期后永久显示处理中

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：生时校正范围终态、跨设备/失败重试、durable 原问题 handoff
- 用户现象：一次继续咨询在输出前失败后，刷新仍无法重试，接口返回“原问题状态已经变化”。
- 触发条件：handoff 处于 `claimed` 或 `executing`，两分钟租约已经过期，客户端重新加载交接。
- 根因：数据库 projection 只看持久化 state，把过期租约仍投影为 `in_progress`；客户端因此不会发起 claim，而执行 RPC 又正确拒绝过期租约，形成永久卡死。
- 修复：projection 将已过期的 `claimed`/`executing` 租约投影为 `pending`，复用既有加锁 claim RPC 原子接管；未过期租约仍保持 `in_progress`，双设备隔离不变。
- 验证：迁移契约测试锁定过期租约恢复语义；生产制造过期 claim 后重新加载、claim、执行模型咨询和 settle。
- 防复发：所有租约型状态的读取投影必须同时解释 lease deadline，不允许只依赖枚举 state。
- 相关记录：BUG-017、BUG-018
- 复发自：无
- 修复版本：待提交

## BUG-020 | 生时校正把语言问答包装成高阻力卡片表单

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：首页生时校正会话、经历录入、候选核对与更正
- 用户现象：每轮同时出现候选卡、领域按钮、年份与月份下拉、经历回顾卡和确认卡；用户需要理解多层控件才能回答一个问题，移动端尤为费力。
- 触发条件：进入生时校正并提交或更正一条真实经历。
- 根因：后端已有自由文本证据契约，但前端仍用结构化表单和多卡片包装；校正叙事 Agent 也未加载 Jyotish Skill 来生成自然、逐问式的取证措辞。
- 修复：改为一段助理提问加一个自然语言输入框；候选状态和证据历史收进可展开进度区；保留明确确认、更正、持久化、计费、计算和分钟验证门禁；叙事 Agent 加载 Jyotish Skill，但服务端技术包仍是候选事实和确认权限的唯一来源。
- 验证：语言优先组件静态与真实 Chromium 390px 回归 8/8 通过；校正路由与叙事契约 23/23 通过；目标文件 ESLint 和 Next.js production build 通过。
- 防复发：语言问答不得重新拆成领域按钮或日期下拉；Skill 只能改进问题策略与措辞，不得生成、重算或确认候选时间。
- 相关记录：BUG-008、BUG-009、BUG-015、BUG-016、BUG-017
- 复发自：无
- 修复版本：待提交（本地可测）

## BUG-021 | 自然语言真实事件在分钟评分入口被静默丢弃

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：生时校正自然语言抽取、历史事件持久化、分钟评分、首轮与兜底叙事
- 用户现象：用户已经提供带日期的真实经历，系统仍反复索取证据；首轮回答展示完整 D 层技术清单，却没有用一个具体问题推进取证。19 世纪事件、疾病、手术、事故和丧亲尤其容易无法参与评分。
- 触发条件：日期早于 1900 年；事件属于健康或重大压力；累计有效事件超过 6 条；或叙事模型未满足首轮全量技术层合同而进入确定性兜底。
- 根因：前端日期正则写死 1900–2099；健康类关键词落入 `other`，并在路由中被过滤，尽管后端已有 `health_pressure` 与 D30 评分支持；路由另有独立的 6 条截断；叙事校验强制首轮正文列出全部稳定层、敏感层和值。
- 修复：日期抽取支持 1000–2099 的四位历史年份；健康、事故、丧亲映射到既有 `health_pressure`/D30 合同并贯通持久化、旧数据导入和公开 turn schema；评分截断统一复用 8 条收敛上限；技术包和 validation receipt 继续完整保存，但非最终用户正文只呈现候选范围、未确认边界和一个高信息量问题，确定性兜底也遵守相同语言交互。
- 验证：抽取、叙事、路由聚焦测试 59/59 通过；真实案例回放、编排和端到端契约 65/65 通过；目标文件 ESLint、Python replay/compilation、`git diff --check` 和 Next.js production build 通过。公开 smoke 中 Steve Jobs、Einstein、Marie Curie 分别保留 4、3、4 条可评分事件，产品过滤结果与结构化 oracle 一致。
- 防复发：新增 18xx 中文与 ISO 日期、健康/事故/丧亲、8 条事件上限和单问题兜底断言；技术层可进入服务端证据包，不得重新进入普通会话正文；family/other 仍是持久化背景，不得伪装成已评分领域。
- 相关记录：BUG-008、BUG-009、BUG-015、BUG-016、BUG-020
- 复发自：BUG-020
- 修复版本：待提交（本地可测）

## BUG-022 | 生时校正入口等待首轮请求完成后才切换会话

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：首页生时校正入口、普通咨询中的“先完成生时校正”、侧栏恢复校正会话
- 用户现象：点击生时校正后长时间停留在首页或原咨询 session，直到恢复、建案、计算和会话持久化全部完成才突然跳转，用户容易误以为点击无效并重复操作。
- 触发条件：`start`、`resume`、durable handoff 或 session persistence 任一请求响应较慢。
- 根因：`openBirthTimeRectification` 虽然先设置了 loading，但专属 session 的插入、激活和校正 surface 的开放都位于首个异步请求之后；surface 还要求首个 turn 已存在，因此 loading 状态无法在目标会话中显示。
- 修复：创建或复用专属 session 后，在任何 `await` 之前立即插入并激活该 session；校正 surface 允许以空 turn 渲染既有“正在建立校正记录…”状态；增加同步 in-flight 门禁防止快速重复点击发出多个启动请求；失败时新建 session 回滚到来源会话，复用 session 则保留可见错误与重试入口。
- 验证：`frontend/tests/consultation-entrypoint.test.ts` 21/21 通过，锁定 session 插入、激活和 loading surface 必须早于首个异步请求，并锁定单请求门禁；目标文件 ESLint、`git diff --check` 和 Next.js production build 通过；真实应用内 Chromium 从首页点击时，在后台恢复完成前已经显示“正在建立校正记录…”，从普通会话切回校正 session 也立即显示目标会话。
- 防复发：首页卡片、普通 session 建议和侧栏恢复必须继续共用同一启动函数；不得重新用首个 turn 是否返回作为 session 可见性的条件。
- 相关记录：BUG-016、BUG-020、BUG-021
- 复发自：无
- 修复版本：待提交（本地可测）

## BUG-023 | 初始化地址保存后的加载提示仍指向生时评估

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：新用户初始化流程、出生地点保存后的全屏加载提示
- 用户现象：用户填完出生地址后，页面实际准备进入首页，但加载提示仍显示正在生成生时评估，造成流程去向与界面文案不一致。
- 触发条件：初始化流程完成出生时间填写，并提交最后一步出生地点。
- 根因：出生时间保存和出生地点保存共用 `saving_profile` 展示阶段；该阶段文案仍按旧流程描述为即将生成生时评估。
- 修复：新增独立的 `entering_home` 展示阶段，仅在 `saveOnboardingPlace` 提交地址时使用，显示“正在进入首页 / 出生资料已保存，正在为你准备首页。”；出生时间保存继续使用原 `saving_profile` 阶段。
- 验证：聚焦测试锁定地址提交与 `entering_home` 的绑定及目标文案；目标文件 ESLint 与 `git diff --check` 通过。
- 防复发：初始化步骤的加载文案必须绑定实际导航结果；不得通过修改共享 `saving_profile` 文案改变出生时间提交阶段的语义。
- 相关记录：BUG-022
- 复发自：无
- 修复版本：待提交（本地可测）

## BUG-024 | 侧栏会话标题与更多操作被拆成两块

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：聊天记录侧栏、当前会话选中态与更多操作入口
- 用户现象：会话标题显示在一块选中背景中，右侧更多操作却以独立圆形按钮悬在外侧，看起来像两个不一致的控件。
- 触发条件：侧栏展开并选中任意会话。
- 根因：选中背景只应用在左侧 `.session-main`，右侧 `.session-menu-trigger` 又单独使用 `50%` 圆角和悬停背景。
- 修复：把选中、悬停和聚焦背景统一应用到整行 `.session-row`；子按钮保持透明，并移除更多操作按钮的独立圆形底色。
- 验证：侧栏契约测试锁定整行选中背景、透明标题按钮和非圆形更多操作按钮；目标文件 ESLint 与 `git diff --check` 通过。
- 防复发：会话标题和行内操作必须共享同一个行级状态面，不得分别绘制互相竞争的选中背景。
- 相关记录：无
- 复发自：无
- 修复版本：待提交（本地可测）

## BUG-025 | 健康压力追问被数据库误判为校正操作冲突

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：生时校正首条自然语言回答、`POST /api/birth-time-conversation`、Supabase 对话持久化契约
- 用户现象：用户提交一条带年月的真实经历后等待约一分钟，接口返回 `409 action_conflict`，页面提示加载最新进度后重试；重复提交仍无法进入下一问。
- 触发条件：技术包为下一轮选择 `health_pressure`（健康与重大压力）作为待补证据领域。
- 根因：应用层已把 `health_pressure` 作为正式领域，并允许语言问答每轮只追问一个重点领域；durable SQL 既缺少该领域，又要求 evidence request 至少包含两个领域。完整计算和叙事生成完成后，`save_conversational_rectification_turn` 才以 `conversational_action_conflict` 拒绝公开 turn。
- 修复：新增向前迁移，将 `health_pressure` 同步加入四个 durable validator 和事件证据表约束，并把 evidence request 基数从 2–4 对齐为应用契约的 1–4；保留现有幂等、版本和候选确认门禁。
- 验证：真实浏览器复现确认只有 `conversational_rectification_valid_evidence_request` 失败，其余公开 turn 子结构、事件、回执和私有候选均通过；迁移应用到测试 Supabase 后，用同一条“2023 年 3 月离家来北京工作”重放，`POST /api/birth-time-conversation` 返回 `200`，日志为 `actionKind: answer`、`resultCategory: success`，事件规范化保存为 `2023-03 · 离家来北京工作`，页面继续自然追问学业经历且输入框恢复可用；聚焦迁移测试锁定四个 validator 与表约束必须共同支持该领域。
- 防复发：应用 evidence domain 枚举新增值时，必须同时更新 TypeScript schema、公开 recap/request、私有候选、事件表约束和迁移契约测试；不得把正常领域扩展映射为通用 409。
- 相关记录：BUG-007、BUG-020、BUG-021
- 复发自：BUG-007
- 修复版本：待提交（测试 Supabase smoke 通过）

## BUG-026 | 首页与会话改版后旧测试阻断生产发布门禁

- 状态：resolved
- 首次发现：2026-07-22
- 最近更新：2026-07-22
- 影响面：production 发布门禁、首页主题入口、会话输入区、生时校正组件服务端渲染测试
- 用户现象：production 应用构建成功，但完整前端测试有 7 项失败，导致最新 `main` 无法通过发布前验证。
- 触发条件：运行完整前端测试；旧断言仍查找已移除的首页证据预览、固定 180px 模型菜单、无条件输入区类名和旧 `profile` 文案来源；旧手动 workflow 还固定在 Node 20，而当前 `@mastra/core` 明确要求 Node 22.13 以上。
- 根因：首页与普通 session 的布局和文案已经更新，测试契约没有随产品行为同步；`Jyotish Skill Tests` 的 Node 版本也落后于其他 production 门禁和应用依赖声明，使 Node 20 把 GSAP ESM 错误解析成 CommonJS namespace。
- 修复：测试改为锁定当前首页主题选择、内容自适应模型菜单、带首页修饰类的停靠输入区和 `profileDraft` 文案来源；GSAP 使用正式命名导出；手动 production 测试 workflow 与其余门禁统一到 Node 22。
- 验证：6 个相关测试文件、Node 22 完整前端测试、ESLint、production build 与 patch check 全部通过后方可发布。
- 防复发：产品 UI 结构调整时必须在同一提交同步源码契约测试；workflow 的 Node 主版本不得低于已锁定运行时依赖声明的最低版本。
- 相关记录：BUG-022、BUG-024、BUG-025
- 复发自：无
- 修复版本：待提交（production gate）
