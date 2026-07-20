# Jyotisha 香港 Staging 服务器设计

日期：2026-07-20

## 目标

把香港服务器 `118.26.111.127` 建设成与生产隔离的 staging 环境，用于验证 GitHub 自动部署、空数据库重建、Supabase 解耦和迁出演练。迁移阶段完成后，这台服务器可停止 staging 服务并转为第三方文字模型 generation worker。

本设计不修改当前生产服务器、`jyotisha.chat` DNS 或生产 Supabase 项目。

## 环境边界

| 项目 | Production | Staging |
| --- | --- | --- |
| 域名 | `jyotisha.chat` | `staging.jyotisha.chat` |
| 服务器 | 现有生产 VPS | `118.26.111.127` |
| GitHub Environment | `production` | `staging` |
| 部署密钥 | production 专用 | staging 专用 |
| 应用配置 | `.env.production` | `.env.staging` |
| Supabase | 生产项目 | 独立 staging 项目 |
| 部署触发 | 手动 production workflow | `staging` CI 成功或手动触发 |

staging 不得写入生产数据库，不得复用 service-role key、数据库密码、SSH 私钥或模型计费密钥。模型接口优先使用独立测试 key、低额度或 provider sandbox。

## 服务器基础设计

- 操作系统：Ubuntu 24.04 LTS x86_64。
- 访问：供应商默认 SSH 用户为 `ubuntu`；本机管理密钥只授权给 `ubuntu`，GitHub deploy 密钥只授权给 `deploy`。两个 key 登录都验证成功后再关闭 SSH 密码登录和直接 root 登录。
- 内存：2 vCPU / 4 GB RAM，增加 4 GB swap；staging 部署串行执行，避免构建峰值并发。
- 防火墙：只开放 SSH、80、443；Python API 5200 和 Next.js 3000 只在 Docker 网络暴露。
- 运行时：Docker Engine、Buildx 和 Compose plugin，从 Docker 官方 apt repository 安装。
- 目录：应用位于 `/opt/jyotisha-staging`，`.env.staging` 权限为 `0600`，不由 rsync 或 Git 覆盖。
- 运维：启用安全更新、日志轮转、磁盘/内存监控；部署前后记录 Docker 状态和健康检查。

## DNS 与 TLS

在域名供应商创建：

```text
A  staging.jyotisha.chat  118.26.111.127
```

Compose 通过 `SITE_ADDRESS=https://staging.jyotisha.chat` 配置 Caddy。DNS 生效后由 Caddy申请和续期 TLS 证书。生产根域名记录保持不变。

## 应用配置

现有 Compose 固定引用 `.env.production`。实施时应使同一份 Compose 接受一个显式配置文件参数，production 默认行为保持不变，staging 指向 `/opt/jyotisha-staging/.env.staging`。不复制一整份长期漂移的 Compose 文件。

staging 配置包含：

- 独立 Supabase URL、anon key、service-role key、DB URL；
- `SITE_ADDRESS=https://staging.jyotisha.chat`；
- staging 专用 admin email 和模型 key；
- 明确的 environment 标识，防止邮件、计费或任务误指向 production；
- 与生产不同的 cookie/session 名称或域范围，避免浏览器 session 混淆。

## GitHub 部署设计

新增 `staging` GitHub Environment：

- Secret：`STAGING_SSH_PRIVATE_KEY`；
- Variable：`STAGING_HOST=118.26.111.127`、SSH port/user/path、staging URL；
- GitHub Environment 只允许控制器分支 `main` 使用；`workflow_run` 另外强制上游成功运行来自 `staging`，并部署其 `head_sha`；
- staging 部署使用独立 concurrency group，不能阻塞或取消 production。

部署流：

```text
push staging
  -> Jyotish Skill CI
  -> checkout 已测试 SHA
  -> 记录旧 SHA 和镜像 ID
  -> rsync 到 /opt/jyotisha-staging（排除所有 .env*）
  -> 校验 .env.staging 权限、固定选择器和 Compose 配置
  -> docker compose build/up
  -> login、401 account、Python health smoke tests
  -> 记录部署 SHA
```

数据库 migration 不隐式混入普通应用部署。迁移必须是单独、可见、可审计的步骤，先在 staging DB 执行并验证，再决定 production 运行窗口。

## 错误处理与回滚

- SSH、rsync、build 或 health check 任一步失败，workflow 必须失败并保留日志。
- 新容器健康检查未通过时，不宣告部署成功。
- 部署前记录当前 SHA 和镜像；应用回滚恢复到上一已验证 SHA。
- 数据库 migration 必须有独立备份和恢复演练。应用回滚不能被误认为数据库回滚。
- Caddy、web、api 中任一服务不健康时，保留 SSH 故障排查通道，不自动删除 volumes 或环境文件。

## 验收测试

服务器基础验收：

- ubuntu admin key 与 deploy key 分别登录成功，密码/root 登录按设计受限；
- UFW 与云防火墙只开放预期端口；
- Docker/Compose 正常；swap 生效；重启后容器能恢复。

部署验收：

- `https://staging.jyotisha.chat/login` 返回成功；
- 未登录 `/api/account` 返回 401；
- web 容器能访问私有 Python `/api/health`，且 Swiss Ephemeris 可用；
- staging 页面与 cookie 不影响 production；
- GitHub 显示 staging deployment 和部署 SHA；
- 故意部署一个失败健康检查的测试 revision 时，workflow 能阻止其被标记为成功。

数据隔离验收：

- staging 注册用户只出现在 staging Auth；
- profile、chat、credits、redemption、jobs 均只写 staging DB；
- staging service role 无法连接 production project；
- staging migration 可从空库重建到当前版本。

## 分阶段实施

1. 通过云厂商控制台确认系统、架构、磁盘、网络和救援入口。
2. 初始化 SSH、安全更新、deploy 用户、swap、防火墙和 Docker。
3. 建立独立 Supabase staging 项目和 `.env.staging`。
4. 配置 `staging.jyotisha.chat` DNS 与 Caddy TLS。
5. 参数化 Compose 配置文件选择，不改变 production 默认路径。
6. 新增 GitHub staging Environment 和 deployment workflow。
7. 手动首部署并验收，再启用分支自动部署。
8. 完成空库 migration、恢复和 Supabase 解耦演练。
9. staging 使命完成后，重新设计并切换为私有 generation worker；不直接把公开 staging 容器当作生产 worker。

## 非目标

- 本阶段不迁移生产用户或生产数据库。
- 不改变 production 自动部署。
- 不购买或部署国内后端服务器。
- 不在本机运行大模型。
- 不在 staging 和 production 之间做应用双写。
