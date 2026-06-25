# Antigravity AI Dasha/Shadbala 真实进度仪表盘建议 (Round 16)

当前，Trust Center 中的披露只有枯燥的红线拦截文案。为了激励开源社区提供截图，建议在首页或 Evidence Intake 面板增加如下真实的“游戏进度条”：

| 指标 | 当前值 | 用户解释 | 数据来源 |
|---|---|---|---|
| **Total template cases** | 5 | “我们的第一期挑战目标数量” | `oracle_collection_queue.py` 的 summary 返回值 |
| **Valid packets** | 0 | “目前有几份被成功收集的绝密截图卷轴” | `oracle_collection_queue.py` 的 summary 返回值 |
| **Ready for calibration** | 0 | “我们有几个数据已经纯净到可以用于修补引擎” | `oracle_collection_queue.py` 的 summary 返回值 |
| **Production tuning allowed** | false | “当前严禁修改全局力量常数，因为数据量未满 5” | `oracle_collection_queue.py` 的 summary 返回值 |
| **D1/D9/SAV confidence** | High / 已验收 | “基础盘我们已有 100% 把握” | 静态固定声明 |
| **Dasha boundary calibration** | 0/3 cases | “大运时间起点的悬赏进度” | 根据那三个关联了 `vimshottari_start_date` 的任务进度计算 |
| **Shadbala absolute calibration** | 0/4 cases | “力量常量的悬赏进度” | 根据那四个关联了 `shadbala_components` 的任务进度计算 |

设计思路：与其藏着掖着，不如把 `valid_packets: 0` 做成大屏进度条。极客一看到 0/5，自然会激发出拿出 JHora 来帮忙“填坑”的冲动。
