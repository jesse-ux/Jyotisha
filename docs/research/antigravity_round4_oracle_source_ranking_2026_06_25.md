# Antigravity AI 外部 Oracle 来源可信度分层 (Round 4)

## 可信度与使用边界分层矩阵

在完善 Dasha、Shadbala 等印度占星高级技法的过程中，必须引入外部基准（Oracle）进行对齐。为避免版权/许可证纠纷，并确保数据的公允性，特将候选参考工具按如下分层规范：

| 来源 | 许可证/使用边界 | 可采集字段 | 不适合作为真值的字段 | 推荐状态 |
|---|---|---|---|---|
| **JHora (Jagannatha Hora)** | 闭源/免费商业软件，**仅限人工查阅截图或手动录入数据** | Dasha start boundary, Shadbala 六大分量, D1/D9 落座与黄经, Ayanamsa 切换效果 | 任何试图批量逆向工程的脚本抓取、反编译逻辑 | `preferred_external_oracle` |
| **PyJHora** | **AGPL-3.0**，**严禁复制实现代码/公式常量/内部查表**，仅限当作黑盒运行 | 黑盒环境下的 Shadbala 各分项数值, Dasha 时间线推演 | 任何内部计算源码和业务逻辑 | `preferred_external_oracle` |
| **VedAstro SDK / API** | MIT 开源，允许安全集成和提取 | 行星黄经 (sidereal longitudes), 基础排盘元数据及 API 结构参考 | 免费版 API 不稳定情况下的 Dasha / Shadbala 等耗时运算输出 | `secondary_external_check` |
| **Swiss Ephemeris** | GPL/开源双重许可，本项目底层依赖。此处指其官方文档作为天文学概念参考 | 岁差 (Ayanamsa) 定义 / 恒星时 (Sidereal Mode) 开关常识 | Dasha 的历法年制推演、Shadbala 占星算法分量 | `display_reference_only` |
| **AstroSage / Prokerala** | 商业化 C 端应用，纯黑盒无开放接口 | 前端展示对标、交互流程、排盘图表 UI 设计参考 | Dasha / Shadbala 作为真值的精确计算来源 (不具备开放可追溯性) | `not_suitable` |

## 分层使用规则
- **`preferred_external_oracle`**：作为我们 `external_verified` 靶心的首选来源，必须在 `reference_note` 中详细写明取样版本及方式。
- **`secondary_external_check`**：作为基础天体位置回归漂移监控的备用来源。
- **`display_reference_only`**：不可用于写死测试靶心数值，仅用于说明性文案和底层配置项解释。
- **`not_suitable`**：不可写入任何 `dasha_shadbala_oracle_cases.json` 作为判据。
