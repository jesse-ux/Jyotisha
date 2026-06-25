# Antigravity AI 给 Codex 的 Round 15 任务建议 (Round 14)

目前系统准确率引擎万事俱备，仅欠打通“导入并落地”这一核心动脉。请 Codex 在 Round 15 重点执行以下动作：

## 1. 增设外部截图工件存放规范
- **文件**：新建目录 `references/oracle/artifacts/` 和 `docs/oracle_collection_guide.md`
- **动作**：创建存储真值证据图片（如 `jhora_jobs_dasha_v1.png`）的合规物理路径，并在 `README.md` 与 Git 中声明不追踪未经脱敏的私人截屏。

## 2. Evidence Packet 前端导入及实时校验（核心闭环）
- **文件**：`jyotish-app/main.js` 和 `scripts/jyotish_api_server.py`
- **动作**：在现有的 `Oracle Evidence Intake` 旁边或下方加上上传表单，桥接至后端的 `oracle_evidence_validator.py`。
- **验收命令**：向本地前端注入并提交填好的测试 JSON，网页上须出现类似 `valid_packets: 1, 状态：过审并提示人工PR` 的绿色弹窗。

## 3. 手工肝出第一张 external_verified 真值表
- **文件**：`references/oracle/dasha_shadbala_oracle_cases.json`
- **动作**：不再停留在自动化纸上谈兵。请根据刚才产出的 SOP，用虚拟机跑一把 JHora，亲自把 `template_steve_jobs_dasha_lahiri` 填满，并将状态手动置为 `external_verified`。
- **验收命令**：`python3 scripts/oracle_evidence_validator.py --queue-file ...` 返回 `valid_packets: 1` 和 `ready_for_calibration: 1`。

## 4. 提升 Shadbala 力量表真值检验粒度
- **文件**：`scripts/oracle_evidence_validator.py`
- **动作**：力量值的校验不能只停留于检查 `shadbala_components` 是否为空，而应该升级为强制检查六分量（Sthana, Dig, Kala 等）是否都有合规的浮点数键值。
- **验收命令**：传入一个仅写了部分分量的伪造 JSON，校验器抛出红灯警告。

## 5. 将技法优先级暴露给普通用户
- **文件**：`jyotish-app/main.js` (Trust Center)
- **动作**：将 Round 13 排出的技法缺口矩阵（如合婚未支持、KP 未实现）同步成一行行醒目的 TODO 清单并展现给用户。
- **验收标准**：用户点击面板能知晓产品上限在哪里。
