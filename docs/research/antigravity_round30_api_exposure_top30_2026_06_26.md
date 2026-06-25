# Antigravity AI API 高 ROI 暴露 Top 30 (Round 30)

## 让路由网连通孤岛

1. **`/api/tajika`**：年运盘。调用已存在的 `varshaphala.py`，接收生辰 + 预测年份。
2. **`/api/jaimini/chara_dasha`**：调用 `jaimini_core.py` 里的流年大运逻辑。
3. **`/api/dasha_list`**：返回该用户适用的条件大运（如 Chaturashiti Sama Dasha 等），而不仅是默认的 Vimshottari。
4. **`/api/matchmaking`**：聚合 `/api/synastry` 的 36 分合婚与尚未暴露的 Kuja Dosha 抵消计算。
5. **`/api/muhurta/month`**：封装批量查询，解决逐日查太慢的问题。
6. **`/api/chart/export/pdf`** (如果用后端生成的话)：这是一个增值商业接口。
7. **`/api/health`**：纯粹用于 Docker 和 CI 存活探测的 200 OK 接口。

## 状态
`已成立`
