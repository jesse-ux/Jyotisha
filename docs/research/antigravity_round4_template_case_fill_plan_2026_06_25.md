# Antigravity AI Oracle 模板逐项填充路线 (Round 4)

## 模板采集计划表

以下是 `references/oracle/dasha_shadbala_oracle_cases.json` 中当前处于 `template_only` 状态的 5 个基准用例的后续填补路径：

| case_id | 当前 status | 缺失字段 | 首选外部来源 | 采集步骤 | 升级为 external_verified 的判据 | 风险 / 阻碍 |
|---|---|---|---|---|---|---|
| `template_private_oracle_redacted` | `template_only` | `moon_sidereal_longitude_deg`, `vimshottari_start_date`, `shadbala_components` | JHora / PyJHora | 手工在 JHora 中排入此 REDACTED_YEAR 样本，提取其月亮黄经与 Shadbala 的详细六大分量，同时记录大运起点。 | 所有 null 字段都已被来自外部软件提取的确定数值替换，并附上带有抓取版本的说明。 | `blocked_by_external_tool_access` (若本地环境无法运行 JHora/PyJHora) |
| `template_steve_jobs_dasha_lahiri` | `template_only` | `vimshottari_start_date`, `shadbala_components` | JHora / PyJHora | 对比开源社区流传或本人 JHora 中输入 Steve Jobs (1955-02-24 19:15) 的大运界限和力量分量。 | 填补精准到日的起运日期与组件级力量靶心，确保节点匹配。 | 坊间流传的 PDF 可能在出生时间(如分钟数)上有微调差异 |
| `template_redacted_place_shadbala_raman` | `template_only` | `moon_sidereal_longitude_deg`, `shadbala_components` | VedAstro API / JHora | 发送 HTTP 请求或人工在 JHora 切换至 Raman Ayanamsa，记录月亮落座及力量值。 | 明确获得 Raman Ayanamsa 下力量值的改变，写入并确认为非本地生成。 | `blocked_by_api_limit` (若 VedAstro 高级功能超时) |
| `template_extreme_latitude_kp` | `template_only` | `ascendant_longitude_deg`, `shadbala_components` | PyJHora | 利用黑盒运行 PyJHora，提取 65° 极高纬度下的上升黄经及由此引发的各分量变动。 | 上升度数及受日出/时区影响的分量（如 Kala Bala 等）被准确回填，标明日出算法假设。 | `blocked_by_external_tool_access` |
| `template_historical_epoch_lahiri` | `template_only` | `sun_sidereal_longitude_deg`, `vimshottari_start_date` | JHora Offline Tool | 利用 JHora 脱机版本排查 1800-01-01 样本，规避现代网络 API 可能缺乏的历史数据库。 | 太阳黄经和 Vimshottari 能够回溯成功并写入 JSON。 | 历史时区与现代系统 UTC 转换逻辑存在巨大鸿沟 |

**核心准则：**
不允许把 `template_only` 谎报成已完成；任何由当前项目引擎本身输出的填补数据只能标记为 `local_baseline` 仅作回归使用，绝不能打上 `external_verified` 的标签。
