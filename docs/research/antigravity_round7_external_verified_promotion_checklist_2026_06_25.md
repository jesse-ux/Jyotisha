# Antigravity AI 外部真值晋级清单 (Round 7)

## 晋级 `external_verified` 前的采集与填报指南

所有 `template_only` 状态的数据在晋级为正式可用靶心（`external_verified`）以解除调参限制前，必须严格完成真实外部环境的采集，并将取得的证据（Evidence）无缺漏地填入 JSON。

### 1. 采集流程与红线

*   **JHora / Jagannatha Hora**：使用 Windows 环境或虚拟机运行正版 JHora。**必须手动截屏**保存带有完整设置参数界面和时间戳的截图（存为 `source_artifact`）。
*   **PyJHora**：利用隔离的沙箱环境运行，并将截取的 stdout 终端输出作为 `source_artifact`。**红线**：PyJHora 的 AGPL 协议意味着其底层 `pyswisseph` 包装逻辑、预先写死的数据表绝对不可抄袭或挪用至本项目，仅仅只是提取最终浮点数结果作为对照。
*   **VedAstro HTTP/SDK**：调用免费 API 或 SDK 获取基础行星落座、黄经。**红线**：由于其可能发生服务端超时、拥堵，故作为补充交叉参照，而非常数校对的第一真理。

### 2. 必须填写的元数据字段 (Metadata)

在 JSON 证据包中，必须填满以下字段：
*   **`tool_name`**: 采集使用的外部工具名称（如 "JHora" 或 "VedAstro API"）。
*   **`tool_version_or_url`**: 具体工具版本（如 "v8.0"）或请求的 URL Endpoint。
*   **`capture_date`**: 执行采集行动的本地日期时间（如 "2026-06-25T12:00:00Z"）。
*   **`source_artifact`**: 指向本地 `/references/oracle_artifacts/` 下的截图文件名或文本输出日志。
*   **`ayanamsa`**: 运行采集时在外部软件里配置的岁差模式（如 "lahiri" 或 "raman"）。
*   **`node_mode`**: 南北交点的配置（"true" 或 "mean"）。
*   **`timezone`**: 时区参数。
*   **`operator_note`**: 操作人的背书与额外声明（如日出算法的配置等）。

### 3. 必须补齐的目标靶标 (Targets)
每个 template_cases 会要求特定的 `missing_target_fields`，如 `moon_sidereal_longitude_deg`、`vimshottari_start_date`、`shadbala_components`。晋级前必须将所有的 `null` 替换为真实采集到的确定值。只有**元数据齐全**、**证据文件挂载**、**占位符消灭**、且**状态标记为 `external_verified`** 时，该包才会通过 `oracle_evidence_validator.py` 的校验。
