# Antigravity AI Tajika / Varshaphala 缺口总表 (Round 29)

## 年度推运僵局

| 检查点 | 当前状态 | 改进路径 |
|---|---|---|
| **算法实现** | 存在于 `scripts/varshaphala.py` | 代码已备好，能够计算当年太阴/太阳返照。 |
| **API 端点** | ❌ 缺失 | 在 `jyotish_api_server.py` 新增 `/api/tajika` 接收 `year` 参数。 |
| **Muntha (年界点)** | ✅ 后端计算完备 | 需透传给 API JSON。 |
| **Varsheshvara (年度星)** | ✅ 后端计算完备 | 需透传给 API JSON，它是判断该年基调的核心。 |
| **Tajika Yogas (古典组合)**| ❌ 缺失 | 需要加入 Ishraf, Muthasil 等十六种特殊相位组合判断。 |
| **前端入口** | ❌ 缺失 | 必须在顶部导航栏加一个 "Yearly Horoscope" (年运) Tab。 |
| **测试断言** | ❌ 缺失 | `local_accuracy_report` 没有任何对 Tajika 准度的检测靶标。 |

## TDD 要求
下一轮必须让 Codex 把 API 路由打通。没有路由的模块等于没有代码。

## 状态
`部分成立`
