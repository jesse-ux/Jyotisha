# Antigravity AI 端到端 E2E 自动化测试补充设计 (Round 29 Extra)

## UI 极度脆弱
目前只有 `run_quality_gate.py` 是测后端的。就算后端算对，前端如果有 JS undefined 导致白屏，用户还是觉得你的软件不能用。

## Playwright 蓝图
必须编写一个 `tests/e2e/test_main_flow.spec.js`：
1. 拦截 HTTP `/api/chart` 接口。
2. 自动填入 1990-01-01 12:00:00，经纬度 28/77。
3. 点击 Submit。
4. 捕捉 `svg` 节点中是否成功渲染了 `Asc: Aries`。
5. 捕捉大运表是否出现。

这是防止 Codex 修代码把前端改挂的最强防线。

## 状态
`未成立`
