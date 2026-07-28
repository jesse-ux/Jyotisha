# BLOCKED

- 真实收信端到端验收：执行环境没有可识别的 staging 测试邮箱/收件箱变量，仓库只记录发信配置而未提供受控测试邮箱。按任务硬规则不使用他人邮箱；代码、测试和部署继续，部署后的注册、验证码登录与忘记密码真实收信步骤待具备受控邮箱后补验。
- PostgreSQL 事务反向测试：当前执行环境没有 `docker`、`postgres`、`initdb`、`psql`、Podman/Colima/Lima。`frontend/tests/admin-database.test.ts` 已实现审计触发器故意失败并断言兑换码行数仍为 0 的红灯证据，但本地执行在启动 fixture 前以 `spawnSync docker ENOENT` 阻塞；交由 exact-SHA staging quality gate 的 Docker 环境运行。全量 `npm test` 因同一缺失 Docker 共阻塞 11 项数据库/部署测试，另有 1 项既有真实 DOM 测试因缺 Playwright headless Chromium 阻塞；其余 1031 项通过，skipped/todo=0。
- staging 两角色浏览器冒烟：已确认受控 admin 测试账号存在且是 `user,admin`，但当前执行环境没有其密码或已登录会话；也未提供受控 viewer 账号。不得读取/猜测凭据或使用他人账号。已完成匿名 shell、5 个资源 401、写请求 401 的服务端冒烟；admin/viewer 登录后浏览器冒烟待授权人员提供受控会话后补验。
