# Antigravity AI Vimshottari Dasha 边界日期战役 (Round 15)

Dasha 边界起运点是整个命运推演的时间轴。一旦产生误差，将导致用户在看盘时产生“时空错位”感。下表列出了我们需要严打的核心断点：

| 样本 | 当前字段 | 外部目标字段 | 可能偏差来源 | 推荐采集步骤 |
|---|---|---|---|---|
| **月亮黄经** | `moon_longitude` | `target.moon_sidereal_longitude_deg` | Swiss Ephemeris 核心配置、章动 (Nutation) 计算策略、恒星时算法差异。 | 在 JHora 的基础参数面板，抄录到小数点后至少 5 位。 |
| **Nakshatra / Pada** | 计算得出 | 隐式验证 | 月亮黄经的微小抖动跨越星宿边界。 | 确保截图能清晰照到月亮所落星宿名称及 Pada 序号。 |
| **大运起点** | `vimshottari_start_date` | `target.vimshottari_start_date` | JHora 的年长制式（360 天 / 365.24 天等），这会造成向后几十天的滚雪球误差。 | 在 Evidence 包的 `operator_note` 强注采用的太阳年制式，并抄录起始大运确切日期。 |
| **Antardasha 起点** | 尚未覆盖 | 亟待扩展 | 次级大运的分摊算法在不同软件可能存在不同余数处理。 | 当主大运对齐后，随机抽查深层子运的节点做二次截屏校验。 |
| **年长/时区/秒精度** | 尚未标准化 | 亟待捕获 | LMT 与标准时区的转换，出生地经纬度到秒级的偏移。 | 强制表单录入经纬度和 LMT 偏差设定。 |
| **Ayanamsa 与 node mode** | 采集表必填 | `metadata.ayanamsa`, `metadata.node_mode` | 不同的岁差（如 Lahiri vs Raman）会直接切移黄道起跑线，True node vs Mean node 导致罗睺/计都位置分歧。 | 不得允许默认值，用户必须显式声明这两个选项，并和 JHora 面板设置强一致。 |
