# Antigravity AI API 未暴露能力总表 (Round 29)

## 路由空洞分析

当前 `jyotish_api_server.py` 主要暴露了 `/api/chart`, `/api/synastry`, `/api/panchanga_range`, `/api/muhurta`。
存在大量模块无法通过 HTTP 访问：

| 隐藏模块库 | 应增加的路由 | 请求参数 | 响应期待 |
|---|---|---|---|
| `scripts/varshaphala.py` | `/api/tajika` | 生辰数据, `year: 2026` | 当年的年度盘、Muntha 落点、年度主星。 |
| `scripts/jaimini_core.py` | `/api/jaimini/chara_dasha` | 生辰数据 | Chara Dasha 列表。 |
| `scripts/compatibility.py` | `/api/synastry/porutham` | 两人数据 | 南印 10 项匹配分数。 |
| `scripts/yoga_rules.json` (更复杂的查询) | `/api/yoga/search` | 星座配置查询 | 满足该特征的经典 Yoga 名称。 |
| `scripts/dasha.py` (条件大运) | `/api/dasha/conditional` | 生辰数据 | 返回适用于此人的非 Vimshottari 大运。 |

## TDD 要求
Codex 需要在 `test_api.py` 里直接先写这 5 个端点的 404 测试，然后再补上这些空洞。

## 状态
`部分成立`
