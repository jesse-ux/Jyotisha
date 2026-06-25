# Antigravity AI 1/5 真实样本人工执行单 (Round 19)

**此文档专供人类执行者阅读**，不可交由 Codex 本地脚本跑单，否则防线报错。

1. **样本选择**：必须使用内置的 Steve Jobs 或 REDACTED_YEAR 占位目标，严禁使用志愿者家人的私人出生信息作为破冰用例。
2. **下载正版黑盒**：请在 Windows 实体机或虚拟机中下载最新版 JHora。
3. **输入参数核对**：
   - Date, Time, Timezone（如果是 REDACTED_YEAR 则是东八区，Steve 则是旧金山）。
   - 经纬度：核对小数点。
   - Ayanamsa：确认是 Lahiri。
   - True Node/Mean Node：切到 True Node。
4. **PyJHora 黑盒备选**：如果无法跑 Windows 实体机，请在隔离沙箱跑 `pyjhora` 获取 stdout，但绝不可以把项目内的 `jyotish_engine.py` 输出塞进去。
5. **截图与命名规范**：
   - 截图必须保存为 PNG 格式。
   - 命名为：`jhora_steve_jobs_lahiri_dasha_v1.png`，`jhora_steve_jobs_lahiri_shadbala_v1.png`。
6. **打码清单（红线）**：
   - 如果截图中无意间包含了你的姓名、电脑账号、文件路径、甚至是浏览器其他页签，必须涂抹掉。
   - 确保只露出数值区域和参数面板。
7. **三张核心截图**：
   - 包含 Moon longitude 的 D1 面板。
   - 包含 Vimshottari 起运时间的 Dasha 面板。
   - 包含 七曜六分量 (sthana 到 drik) 细分数值的 Shadbala 面板。
8. **填写 JSON**：
   - 打开 `references/oracle/evidence_packet_templates/jhora_steve_jobs_lahiri_first_packet.json`。
   - 将 `source_artifact` 补全为截图路径。
   - 将 `target.vimshottari_start_date` 和 `target.shadbala_components` 中所有的 null 替换为截图里的真实数字。
   - 将 `status` 从 `"draft"` 改为 `"external_verified"`。
9. **退回重采标准**：
   - 数据填错了小数点。
   - 截图里缺了某一颗星或某一个分量。
10. **交给 Codex**：
    - 完成后，将改好的 JSON 放回队列目录，并提交通知我。
11. **调参前提声明**：
    - 哪怕你完成了这个包，`valid_packets` 变成 1，系统由于 `production_tuning_allowed=false` 仍然会保持冻结，直至收满 5 个为止。
12. **警告**：不要试图写个 Python 脚本去替换人工填报，本项目的核心就是获取那些没有被 Python 污染过的第三方原生界面数据。
