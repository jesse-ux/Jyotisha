# Antigravity AI 异常边界恢复能力 (Round 29 Extra)

## OOM 与超时防范
如果用户恶意提交极端的经纬度（如 `900`），或者查一整年的 Panchanga。

1. **后端输入校验**：在 `jyotish_api_server.py` 第一行用 Pydantic 卡死范围 `lat [-90, 90]`。
2. **算力限制**：限制 Muhurta 和 Panchanga 查询跨度不能超过 31 天。
3. **502 恢复**：当前端请求超时，应该弹出一个“网络波动或算力超限”，而不是永久转圈圈。

## 状态
`未成立`
