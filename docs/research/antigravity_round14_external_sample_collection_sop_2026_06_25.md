# Antigravity AI 真实外部样本采集 SOP (Round 14)

为突破当前 `valid_packets: 0` 困境，保障取证纯净且不触碰 GPL 等传染性协议，所有验证工作必须在严格物理/进程隔离的环境下以纯黑盒形式完成。本 SOP 指导使用者如何产出第一个有效的外部真实样本包。

## 采集红线
1. **PyJHora**: 只能作为黑盒命令输出来源核对数字。**严禁**复制或借鉴其实现代码及内部常量表至本系统，避免 AGPL 感染。
2. **JHora**: 只能作为图形界面手动操作及截图采证的目标。**严禁**任何形式的反向工程其执行体或抽取内存表。
3. **VedAstro**: 尽管为宽松协议，但也只能作为次级黄经校验；因其在 Shadbala 和极高精度 Dasha 上的能力尚未达到权威认证级别，不适合作为唯一 Shadbala 绝对值标尺。

## 操作步骤

### 第一步：开启沙盒并初始化目标
1. 打开一台无其他编程环境的虚拟机（或干净的桌面环境），运行标准版 JHora (v8.0+)。
2. 获取一张我们要处理的答卷：从我们系统中的 Trust Center，点击 `下载 Evidence Packet`，比如下载了 `template_steve_jobs_dasha_lahiri` 包（获得 draft JSON）。

### 第二步：JHora 手工排盘
1. 在 JHora 中手工输入该 JSON 对应的生辰参数（如 1955年2月24日 19:15:00，旧金山）。
2. 在 JHora 设定（Preferences）中，严格对齐 JSON 要求的边界：
   - 岁差 (Ayanamsa) 设为 Lahiri (Chitrapaksha)。
   - 交点模式 (Node Mode) 设为 True Node。
   - 太阳日出边界定义 (Sunrise definition) 记入 `operator_note`。

### 第三步：截图留证
1. 定位到 JHora 包含“月亮黄道黄经度数”和“Vimshottari Dasha 列表起运时标”的主窗体面板。
2. 捕获完整窗口的截图，命名为 `jhora_jobs_dasha_v1.png`（或类似高辨识度命名）。

### 第四步：包内容填报
编辑刚才下载的 JSON 文件，替换掉 `""` 或 `null` 的缺省值：
- `tool_name`: `"JHora"`
- `tool_version_or_url`: `"8.0"`
- `capture_date`: 取当前填表时间的 ISO 格式字符串。
- `source_artifact`: 填入刚才截图保存的具体相对或绝对路径（保证审查者能找到图片）。
- `operator_note`: 写入操作备注（例如：“日出定义采用了默认光盘上缘”）。
- **目标打靶**：
  - `target.moon_sidereal_longitude_deg`: 抄录截图中月亮的精确黄经（转换为浮点度数）。
  - `target.vimshottari_start_date`: 抄录截图中大运的起运日字符串。

### 第五步：运行黑盒校验
1. 将包推入检验环境：`python3 scripts/oracle_evidence_validator.py --queue-file <你编辑的json>`。
2. **晋级失败条件**：
   - 如果 validator 发现你缺了截图路径（红灯）。
   - 如果发现 `tool_name` 等于 `local engine` 或是你的本仓 Jyotish（红灯）。
   - 目标字段未填满（红灯）。
3. 只有当 CLI 打印出 `ready_for_calibration: 1` 和 🟢 无 problems 时，该数据才算合法纯净的真实外部样本，才有资格合并入主分支。
