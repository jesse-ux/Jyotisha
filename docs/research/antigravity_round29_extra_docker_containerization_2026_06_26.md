# Antigravity AI Docker 与部署隔离审查 (Round 29 Extra)

## 生产环境安全隐患
当前只依赖 `npm run dev` 和直接起 python API 极不稳定。占星用户可能在自己的 NAS 或 VPS 部署。

## 容器化设计清单
1. **轻量化镜像**：必须采用 `python:3.11-alpine` 加上预编译的 `swisseph` 和 `flatlib` wheel 减小体积。
2. **Nginx 反向代理**：将 5173 的前端静态包与 5200 的 Python API 整合到一个镜像里，只暴漏 80 端口，解决跨域 CORS 问题。
3. **健康检查机制**：增加 `/api/health`。
4. **日志脱敏**：绝不能把用户的经纬度打在 stdout 日志里，这在 Docker 容器日志中极易泄露。

## 状态
`未成立`
