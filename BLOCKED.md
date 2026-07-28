# BLOCKED

- 真实收信端到端验收：执行环境没有可识别的 staging 测试邮箱/收件箱变量，仓库只记录发信配置而未提供受控测试邮箱。按任务硬规则不使用他人邮箱；代码、测试和部署继续，部署后的注册、验证码登录与忘记密码真实收信步骤待具备受控邮箱后补验。
- PostgreSQL 事务反向测试：当前执行环境没有 `docker`、`postgres`、`initdb`、`psql`、Podman/Colima/Lima。`frontend/tests/admin-database.test.ts` 已实现审计触发器故意失败并断言兑换码行数仍为 0 的红灯证据，但本地执行在启动 fixture 前以 `spawnSync docker ENOENT` 阻塞；交由 exact-SHA staging quality gate 的 Docker 环境运行。全量 `npm test` 因同一缺失 Docker 共阻塞 11 项数据库/部署测试，另有 1 项既有真实 DOM 测试因缺 Playwright headless Chromium 阻塞；其余 1031 项通过，skipped/todo=0。
- staging 两角色冒烟：已确认受控 admin 账号 `luna@copse.life` 存在且是 `user,admin`，但仓库/环境未提供受控 viewer 账号；不得使用他人账号。viewer 浏览器冒烟需先由授权人员创建/指定受控 viewer。
- staging 发布控制器冲突：exact staging SHA `218cee579e92fcf9bfe435a349250cfe23304547` 的 `Staging Backend Quality Gate` run 30322107657 已成功，但既有 `Deploy staging` run 30322719839 与 `Migrate Staging Database` run 30322756154 都在 “Verify reviewed revision and staging target” 拒绝，原因为 `staging revision is not in the reviewed main history`。控制器要求部署 SHA 属于 main 历史，而本任务硬规则明确“不碰 main、最终只合入 staging”；禁止绕过控制器或将功能合入 main，故 migration/deploy/health exact SHA 被此互斥规则阻塞。
