# Jyotisha Web

Jyotisha 是 `yinduzhanxing` 的聊天式消费者 Web 前端。它使用 Next.js App Router 提供用户与 Mastra Agent 的连续问答，同时继续复用仓库现有的 Python 印度占星计算工作流。它不生成固定报告。

## 架构

```text
Browser
  -> Next.js /api/consult
    -> Mastra agent
      -> 按问题语义加载 jyotish-vedic-astrology Skill
      -> consultation tool
        -> Python /api/consultation_workflow
```

- Next.js 只负责产品界面、输入校验和结果呈现。
- Python 服务仍是星盘、分盘、时序与证据计算的事实来源。
- Skill 提供方法、路由和真实性边界；它不会替代 Python 的实际排盘计算。
- Mastra 只能基于工具返回的数据组织语言；工具失败时会明确降级，不生成虚构星位。
- Agent 回答通过 `/api/consult` 以纯文本流返回；前端在收到分片时增量渲染 Markdown，而不是等待整段回答完成。

## 环境要求

- Node.js 20+
- Python 3.11 或 3.12（主项目代码不兼容系统自带的 Python 3.9）
- OpenAI 或兼容 OpenAI Chat Completions 的第三方模型 Key。未配置时仍可返回 Python 引擎摘要，但不会生成完整 AI 解读。
- Supabase 项目，用于邮箱 OTP 登录、咨询点数、一次性兑换码和账务流水。

## 配置

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing/frontend
cp .env.example .env.local
```

`.env.local`：

```dotenv
# Python 占星计算服务
JYOTISH_API_BASE=http://127.0.0.1:5200

# 推荐：多模型目录。目录只保存路由元数据，Key 由 apiKeyEnv 引用。
LLM_DEFAULT_MODEL_ID=deepseek-pro
LLM_MODELS_JSON='[{"id":"deepseek-pro","label":"DeepSeek V4 Pro","description":"更适合复杂分析","provider":"openai-compatible","baseURL":"https://api.deepseek.com","apiKeyEnv":"DEEPSEEK_API_KEY","model":"deepseek-v4-pro","creditCost":1},{"id":"gpt-5-mini","label":"ChatGPT 5 Mini","description":"响应稳定、速度均衡","provider":"openai","apiKeyEnv":"OPENAI_API_KEY","model":"openai/gpt-5-mini","creditCost":1}]'
DEEPSEEK_API_KEY=<server-secret>
OPENAI_API_KEY=<server-secret>

# 兼容旧的单模型 OpenAI 配置
# OPENAI_API_KEY=<server-secret>
# MASTRA_MODEL=openai/gpt-5-mini

# 兼容旧的单个 OpenAI-compatible 配置
# LLM_BASE_URL=https://your-provider.example/v1
# LLM_API_KEY=<server-secret>
# LLM_MODEL=your-model-id
# LLM_PROVIDER_ID=third-party

# 可选：部署目录与本仓结构不同时，显式指定 Mastra Skill 目录
# JYOTISH_SKILL_PATH=/absolute/path/to/yinduzhanxing/skills/jyotish-vedic-astrology
```

第三方端点必须兼容 OpenAI 的 Chat Completions 调用方式，并支持工具调用（function calling），否则 Agent 无法稳定调用占星计算工具。`LLM_MODELS_JSON` 只能填写服务端认可的固定地址和模型；浏览器只会得到模型 ID、名称、说明和点数。密钥只放在 `.env.local`，**不要**加 `NEXT_PUBLIC_` 前缀，也不要提交到 Git。每次修改 `.env.local` 后重启 Next.js 开发服务器。

## Skill 如何触发

不需要输入 `/skill` 命令。Mastra 会先把 Skill 的 `name` 和 `description` 提供给模型；当用户问题与印度占星、解盘、推运、Dasha、Transit、Nakshatra、Yoga 等语义匹配时，Agent 会按需加载完整 Skill，再调用计算工具。

例如，先在“个人资料”中保存出生信息，然后直接发送：

```text
请根据我的出生资料，分析未来一年事业发展和适合跳槽的时间窗口。
```

完整链路是：

```text
用户问题
  -> Mastra 识别并加载 jyotish-vedic-astrology
  -> Agent 依据 Skill 选择工作流
  -> run-jyotish-consultation
  -> Python consultation_workflow
  -> Agent 流式组织聊天回答
```

必须配置可用的模型 Key 才会进入这条链路。没有配置模型时，`/api/consult` 会直接返回 Python 引擎摘要，此时不会运行 Mastra Agent，也不会加载 Skill。可在浏览器 Network 中查看 `/api/consult` 响应头：`x-ayanam-mode: mastra` 表示请求进入了 Agent；`x-ayanam-mode: engine` 表示只运行了 Python 引擎。

仓库根目录的主 `SKILL.md` 通过 `skills/jyotish-vedic-astrology/` 这个 Mastra 兼容目录加载。该目录名必须与 Skill frontmatter 中的 `name` 一致。生产部署时需确保 `SKILL.md`、`references/`、`scripts/` 和 `assets/` 一起存在；如果目录结构不同，请设置 `JYOTISH_SKILL_PATH`。

## 本地启动

先创建并使用项目自己的 Python 3.11/3.12 虚拟环境。这样 `pyswisseph` 会安装在 API 实际使用的解释器中，避免星盘工具因缺少 `swisseph` 降级或报错：

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing
# 首次执行；把 python3.12 换成你机器上可用的 Python 3.11/3.12
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 每次启动 API 都使用同一个虚拟环境
.venv/bin/python scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200
```

如果你的终端没有 `python3.12`，请先安装或定位一个 Python 3.11+ 解释器后再创建 `.venv`；不要使用 macOS/Xcode 自带的 Python 3.9。

再启动 Web：

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing/frontend
npm install
npm run dev
```

默认访问 `http://localhost:3000`。如果该端口已被占用，Next.js 会自动选择下一个可用端口。

## 验证

```bash
npm run lint
npm run build
```

## 当前产品能力

- Supabase 邮箱 OTP 登录；未登录用户不能调用咨询接口。
- 左侧聊天 Session、每个 Session 的消息与更新时间均存储在 Supabase；切换 Session 会将该会话的最近上下文提交给 Agent。
- 出生资料与称呼位于“账户与出生资料”面板，保存后可在同一账号的所有 Session 与其他设备间复用。
- 账户、出生档案、聊天历史、点数和兑换记录均存储在 Supabase，并通过 RLS 限制为用户只能读取和修改自己的数据。
- 出生地点支持中国的国家 / 省级 / 市级 / 县区四级选择，按行政区中心坐标进行星盘计算。
- 没有每日提问次数限制。点击发送后有 2.5 秒免费撤回窗口，此时尚未调用模型或预扣点数。窗口结束后咨询开始并预扣 1 点；首个输出分片前取消会幂等退款，已经收到输出后停止会保留现有内容并正常计费，避免部分回答被无限免费获取。
- Agent 流式回答支持 Markdown 与 GFM 表格。
- 首次进入空 Session 时，Agent 会在聊天区引导填写出生资料。保存后，Mastra 中的 onboarding Agent 会按照 `jyotish-vedic-astrology` Skill 生成欢迎语和事业、关系、时运三个入门问题；结果按版本缓存到 Supabase，同一用户不会在每次刷新时重复消耗模型。每次正式回答则在同一次咨询 Agent 调用中生成三个与当前解读相关的后续问题，并随 Session 保存到 Supabase。


## 中国出生地点数据

个人资料中的出生地点目前覆盖中国的省级、市级与县区级行政区。位置数据为行政区中心点，不是地址级定位；如需更新本地快照：

```bash
cd /Users/jesse/Downloads/Copse/astrology/yinduzhanxing/frontend
PATH="/opt/homebrew/bin:$PATH" npm run data:china
```

数据来源与许可证说明见 `src/data/CHINA_LOCATION_DATA.md`。

## Supabase 账户、点数与兑换码

### 1. 创建项目并配置环境变量

在 Supabase 创建项目后，将 Project Settings / API 中的值写入 `.env.local`：

```dotenv
NEXT_PUBLIC_SUPABASE_URL=https://PROJECT_REF.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ADMIN_EMAILS=admin@example.com,ops@example.com
```

- `NEXT_PUBLIC_*` 只包含允许浏览器使用的项目 URL 和 anon key。
- `SUPABASE_SERVICE_ROLE_KEY` 可以绕过 RLS，只能放在服务端环境变量中，绝不能加 `NEXT_PUBLIC_`、提交到 Git 或展示给前端。
- `ADMIN_EMAILS` 是逗号分隔的管理员邮箱白名单。没有配置时普通账户仍可登录，但 `/admin/codes` 不可用。

### 2. 执行数据库迁移

使用 Supabase CLI：

```bash
npx supabase login
npx supabase link --project-ref PROJECT_REF
npx supabase db push
```

也可以在 Supabase SQL Editor 中执行：

```text
supabase/migrations/20260715000000_account_credits.sql
supabase/migrations/20260715010000_harden_credit_rpcs.sql
supabase/migrations/20260715020000_service_role_table_grants.sql
supabase/migrations/20260715030000_user_profiles_chat_sessions.sql
supabase/migrations/20260715040000_agent_onboarding_cache.sql
supabase/migrations/20260717000000_consultation_request_lifecycle.sql
```

迁移会创建：

- `profiles`：用户点数余额、称呼与出生档案。
- `chat_sessions`：用户的聊天 Session、消息和最近更新时间。
- `redemption_codes`：只保存兑换码 SHA-256 与掩码，不保存完整码。
- `credit_transactions`：兑换、预扣、退款和模型 Token 用量流水。
- `redeem_code`：一次性兑换，使用行锁保证同一码全局只成功一次，并记录兑换账户。
- `consultation_requests`：保存每次咨询的 `reserved` / `completed` / `cancelled` 结算状态。
- `begin_consultation_credit` / `complete_consultation_credit` / `cancel_consultation_credit`：仅允许服务端 `service_role` 调用，通过请求级事务锁保证预扣、完成与退款互斥且幂等。

### 3. 配置邮箱验证码模板

在 Supabase Dashboard 的 Authentication / Email Templates 中编辑 Magic Link 模板，使用验证码而不是登录链接：

```html
<div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;color:#1d1d1f">
  <h2 style="font-size:22px">登录 Stellara</h2>

  <p>你的登录验证码是：</p>

  <div style="margin:24px 0;font-size:32px;font-weight:600;letter-spacing:8px">
    {{ .Token }}
  </div>

  <p style="color:#6e6e73;font-size:14px">
    验证码仅用于本次登录。如果不是你本人操作，请忽略这封邮件。
  </p>
</div>
```

登录页会调用 `verifyOtp({ email, token, type: "email" })` 校验验证码；不要把模板改回 `{{ .ConfirmationURL }}`。还应在 Authentication / URL Configuration 中配置本地和生产站点 URL。

### 4. 创建第一批兑换码

1. 使用 `ADMIN_EMAILS` 中的邮箱登录。
2. 打开 `/admin/codes`。
3. 选择每个兑换码包含的点数、数量、有效期和备注。
4. 点击生成后立即复制完整码；刷新或离开页面后只会保留掩码。

相同兑换码只能兑换一次；首次兑换后会永久记录兑换账户、邮箱和时间。新注册用户默认 0 点，因此即使 demo URL 被转发，也不能在没有兑换码的情况下调用 Agent。

## 当前线上部署

当前生产 Demo 使用 `https://jyotisha.chat`，Next.js、Mastra 和 Python API 通过 Docker Compose 部署在香港 VPS，Supabase 与模型 API 继续使用云服务。服务器、DNS、环境变量、更新和验收命令统一以 [`../deploy/README.md`](../deploy/README.md) 为准。

## Vercel + Supabase 备选部署

以下方案只作为无服务器备选，不是当前线上拓扑。

### Web 部署到 Vercel

将 `frontend` 作为 Vercel Root Directory，并在 Vercel Project Settings / Environment Variables 配置：

```dotenv
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
ADMIN_EMAILS=...
OPENAI_API_KEY=...
MASTRA_MODEL=openai/gpt-5-mini
JYOTISH_API_BASE=https://your-python-api.example.com
```

如果使用第三方模型，则用 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 替换 OpenAI 配置。所有服务端 Key 只配置在 Vercel，不要写进浏览器代码。

### Python 服务必须单独部署

Vercel 上的 Next.js 不能访问你电脑的 `127.0.0.1:5200`。需要把仓库根目录的 Python API 部署到可从公网 HTTPS 访问的服务，例如独立 VM、Railway、Render 或 Fly.io，然后把公开地址写入 `JYOTISH_API_BASE`。

部署完成后依次验证：

```text
1. Python 健康检查和 consultation_workflow 可访问
2. 邮箱 OTP 可以登录
3. 管理员可以生成兑换码
4. 普通账户只能兑换一次
5. 余额为 0 时不能咨询
6. 成功回答扣 1 点
7. Agent/服务端在首个输出前异常时点数退回；已有输出后异常会保留现有内容并正常计费
8. 用户在 2.5 秒撤回窗口内停止时不调用模型、不扣点
9. 撤回窗口结束后、首个输出分片前取消时点数退回
10. 用户已经收到输出后停止时保留已有内容并正常计费
```

## Demo 防滥用边界

当前版本采用“登录 + 兑换码点数”而不是每日次数限制：

- 所有咨询请求必须有有效 Supabase 登录态。
- 余额不足时服务端不会调用模型或 Python 工具。
- 兑换码一次性使用并绑定账号，数据库不保存完整码。
- 预扣和退款只允许服务端 service role 调用，且以 `request_id` 幂等。
- 服务端拦截系统提示词、Skill 原文和密钥提取请求；Agent 也被限制不得给出医疗、法律、投资等安全关键指令或确定性死亡/诊断预测。
- 这不是完整内容审核平台。正式公开投放前，可再增加登录/兑换接口速率限制、验证码防机器人和运营后台封禁能力，但不需要把产品改成“每天最多问几次”。

## 尚未实现

- 微信/支付宝/Stripe 等真实支付与自动发码。
- 管理员禁用尚未兑换的兑换码。
- 完整的风控、审计后台和退款工单。
