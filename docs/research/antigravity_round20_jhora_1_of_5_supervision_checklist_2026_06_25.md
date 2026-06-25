# Antigravity AI JHora 1/5 人工采集监督清单 (Round 20)

人工执行者在录入第一单时，**必须满足以下 12 条军规**：

1. **外部工具环境**：不可用本地脚本跑。必须起一个 Windows 打开正版 JHora。
2. **Steve Jobs 资料**：1955-02-24, 19:15, 旧金山 (-8区)。
3. **参数强校验**：务必确认 JHora 的 Ayanamsa 选中了 **Lahiri (Chitra Paksha)** 且 Node 选了 **True Node**。
4. **Vimshottari 截图**：把 JHora 的 Dasha 栏位日期截下来。
5. **Shadbala 截图**：把 Strength 面板里的 7 行（日到土星）、6 列（sthana 到 drik）截下来。
6. **Artifact 命名**：`jhora_steve_jobs_lahiri_shadbala_v1.png` 等，必须存放于 `references/oracle/artifacts/` 目录。
7. **打码检查**：严禁把电脑用户名、浏览器其它 Tab、QQ/微信弹窗截进去。发现即拒收。
8. **JSON 填写**：打开 `jhora_steve_jobs_lahiri_first_packet.json`。把刚才所有截图里的浮点数抄进去，把 `null` 覆盖。把 `source_artifact` 指向截图。把 `status` 改成 `"external_verified"`。
9. **运行 validator**：执行 `python3 scripts/oracle_evidence_validator.py`。
10. **1/5 成功判据**：如果终端输出 `valid_packets: 1` 并且不再抱怨 `missing` 或 `invalid_type`，即宣告成功。
11. **调参前提边界**：即便 `valid_packets: 1`，由于总量不到 5，`production_tuning_allowed` 仍为 `false`。系统继续锁定调参。
12. **失败退回情形**：如果人类在 JSON 里填了负数、填了百分比而不是 Rupa 分、没打码截图、或把 `tool_name` 空着，统统重做！
