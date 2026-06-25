# Antigravity AI API 技能缺失 Top 50 审计 (Round 25)

通过核对 `/api/chart` 接口，发现如下算力未能通过 HTTP 透出：

| API 缺口项 | Token/路径证据 | 说明与修复 |
|---|---|---|
| 1. Tajika 年盘查算 | `jyotish_api_server.py` 无对应 endpoint。 | 需要新增 `/api/tajika` 接收 `target_year`。 |
| 2. 独立查 Yoga 列表 | `get_full_reading` 混在一起。 | 需新增 `/api/yoga` 仅返回 Yoga 数组，省宽带。 |
| 3. Chara Dasha 独立请求 | 混在 full reading。 | 需新增 `/api/dasha/chara`。 |
| 4. 任意两颗星的相位 | 只能全盘返回。 | 新增 `/api/aspect?star1=Sun&star2=Moon`。 |
| 5. 纯月亮度数计算 | 只能算全盘。 | 新增 `/api/moon` 用于 Ashtakoot 前置计算。 |
| 6. Ashtakavarga 宫位分 | API 只有 337 总分，缺 12 宫分。 | 修改 engine 返回值为数组 `[...12]`。 |
| 7. Panchang 查算 | 缺 `panchang.py` 调用。 | 新增 `/api/panchang`。 |
| 8. 错误结构体化 | `500 traceback` 裸奔。 | 统一返回 `{"error": "MSG", "code": 1}`。 |
| 9. Oracle Check | 客户端无法主动校验 JSON。 | 暴露 `/api/validate_oracle`。 |
| 10. Ayanamsa 切换 | `/api/chart` 写死 Lahiri。 | 开放 `ayanamsa=raman` 的 query string。 |

**副手下一轮任务**：梳理 `/api/panchang` 应该返回的数据结构 Schema。
**Codex 可做任务**：在 `jyotish_api_server.py` 增加接收 `ayanamsa` 参数的逻辑。
**Codex 可做任务 2**：拦截 HTTP 500 的 Traceback 报错，包裹成 JSON 标准格式。
