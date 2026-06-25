# Antigravity AI 外部真值采集表单化方案 (Round 12)

为了突破当前 `valid_packets: 0` 的僵局，我们需要将后台冷冰冰的 `oracle_collection_queue` 任务转换为普通人能看懂、填得来、能上传证据图的可视化操作面板（如 `Oracle Evidence Intake`）。

## 表单字段设计规范

| 字段 | 类型 | 是否必填 | 示例 | 校验规则 |
|---|---|---|---|---|
| `case_id` | 锁定枚举值 | **是** | `template_steve_jobs_dasha_lahiri` | 用户从现有的 5 个待办模板下拉框中选取，不可自造。 |
| `tool_name` | 文本 | **是** | `JHora` 或 `PyJHora` | 明确来源软件名称，不能出现本仓库（`local engine` / `Jyotish Engine`）。 |
| `tool_version_or_url` | 文本 | **是** | `8.0` / `github.com/naturalstupid/PyJHora` | 必须提供版本号或开源库地址以供追溯。 |
| `capture_date` | 日期时间 | **是** | `2026-06-25T14:30:00Z` | 操作人员采集时的 ISO 8601 格式时间戳。 |
| `source_artifact` | 文件路径 | **是** | `/assets/evidence/jhora_jobs_dasha.png` | 必须是一张包含 JHora 排盘结果面板的高清截图，供后人肉眼核查。 |
| `ayanamsa` | 文本 | **是** | `Lahiri (Chitrapaksha)` | 明确操作软件时使用的岁差。 |
| `node_mode` | 文本 | **是** | `True Node` | 明确所选的罗睺/计都计算模式。 |
| `timezone` | 文本 | **是** | `UTC` 或 `Local (+08:00)` | 软件设置时使用的时区标准。 |
| `operator_note` | 文本 | 否 | "注意JHora的日出设置是按光盘上缘计算" | 操作时的额外配置警告或边界条件说明。 |
| `moon_sidereal_longitude_deg` | 浮点数 | 视目标而定 | `234.567891` | 若为黄经采集任务则必填。 |
| `vimshottari_start_date` | 日期 | 视目标而定 | `1980-04-15` | 若为大运采集任务则必填。 |
| `shadbala_components` | JSON 对象 | 视目标而定 | `{ sthana: ..., dig: ... }` | 若为力量采集任务则必填，对应 6 个子维度的浮点数据。 |
| `external_verified` | 状态位 | **底层强控** | `true` | 表单提交后系统自动盖章，但需经过 Validator 黑盒二次清洗。 |

## 严厉实施红线
1. **彻底拒绝自产自销**：如果表单识别到图片为本地引擎界面，或 `tool_name` 等于 `local engine`，将立即熔断该次提交。
2. **知识产权纯净化**：对 PyJHora 和 JHora 只能进行**结果读取（黑盒取数）**，禁止在 `operator_note` 等任何地方粘贴从其他 AGPL 软件抄袭来的算法公式及源码块。
3. **全局调优许可**：只有当 `external_verified` 为 true 的证据包总数满足基准要求后，系统层面的 `production_tuning_allowed` 锁才会开启，否则禁止进行全局缩放与微调。
