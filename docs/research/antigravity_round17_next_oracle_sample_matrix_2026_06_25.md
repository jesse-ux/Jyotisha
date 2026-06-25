# Antigravity AI 下一批 oracle 样本扩展建议 (Round 17)

现阶段不仅需要填坑，更要为下一阶段高级技法的准确度护城河铺路。建议 Codex 预设如下样本列入队列：

| 样本 | 外部来源 | 目标字段 | source_artifact 类型 | 是否需要人工截图 | 风险 |
|---|---|---|---|---|---|
| **Ashtakoot 合婚** | VedAstro (API 兜底) / JHora | `target.ashtakoot_total_score`, `target.nadi_dosha_present` | 网页双盘比对或 JHora 合婚面板截图 | **是** | 各流派对 Nadi 冲克的豁免条件有争议，算错一星全盘毁。 |
| **KP Horary** | VedAstro / 专用 KP 商业软件 | `target.kp_sub_lords`, `target.horary_number_mapped_ascendant` | 软件内 KP 专门面板截图 | **是** | 出生时间哪怕差几秒钟，Sub Lord 就会切星，极容易引起争执。 |
| **Muhurta date-range solver** | JHora | `target.muhurta_auspicious_percentage` | 择日区间曲线图或面板导出 | **是** | 复合条件过多（如 Tara Bala, Chandrabala 交织），目标值极难标准化为纯浮点。 |
| **Bhava Chalit Sripati/Placidus** | PyJHora (纯黑盒 CLI 对照) | `target.house_cusps_longitude_deg` | 命令行输出日志文本 | 否 (可用脚本跑) | 高纬度（极地）下 Placidus 制式的星相异常容易导致崩溃，需要加入极地 Case。 |
| **D24/D30/D60 深分盘模板** | JHora | `target.d60_ascendant_sign` | D60 专用九宫格截图 | **是** | 对时间精度要求苛刻到秒，只能采信有可靠 BTR (生辰校正) 认证的星盘。 |

**执行建议**：在 `references/oracle/dasha_shadbala_oracle_cases.json` 中直接插入这些占位符任务，让我们的收集目标扩大。
