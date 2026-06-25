# Antigravity AI 给 Codex 的 Round 14 任务建议 (Round 13)

在 Round 13 中，我们成功让普通用户能够从 Trust Center 下载到合规的 Evidence Packet 试卷。现在亟需把这份试卷给“收”上来并由我们的铁闸把关。请 Codex 在 Round 14 执行以下优先任务：

## 1. 支持用户导入并现场校验 Evidence Packet
- **执行路径**：在 `jyotish-app/main.js` 中的 Oracle Evidence Intake 面板旁，增设一个“上传填好后的 Packet 验证”按钮，或在 `api_server.py` 新增一个上传验证路由。
- **动作**：用户拖拽一个填好目标值与截屏路径的 JSON 进去，前端调用本地 `scripts/oracle_evidence_validator.py` 并实时显示返回的 `problems` 数组或是 🟢通过字样。
- **验收标准**：提供一个损坏的包和一个合规的包，确保网页上出现正确的阻断红字与放行绿字。

## 2. 补齐黑盒手工采集操作图文指引
- **执行路径**：新建 `docs/oracle_collection_guide.md` 并链接到 Trust Center。
- **动作**：不要触碰 JHora 的任何反编译代码，仅以纯粹的软件操作者身份，截取几张“在哪里点开大运面板”、“如何设置 Lahiri 岁差”、“如何截图”的说明。
- **验收标准**：该指南对从未用过 JHora 的测试人员也具有可操作性。

## 3. 亲自下场填报首张外部真值表
- **执行路径**：无代码修改。纯手工活。
- **动作**：Codex 依据刚才写好的操作说明，在一台隔离机器上打开 JHora，亲手把 `template_steve_jobs_dasha_lahiri` 给做出来。然后把生成的 JSON 和 png 推上仓库。
- **验收命令**：`python3 scripts/oracle_evidence_validator.py --queue-file ...`，看到 `valid_packets: 1` 的历史性突破。

## 4. 将高阶技法矩阵同步进前端及离线报告
- **执行路径**：修改 `jyotish-app/export.js` 和 `main.js`。
- **动作**：不仅告知用户哪些在校准，还要告知用户本系统当前压根还没实现的盲区（如合婚、KP 等），将坦诚进行到底。
- **验收标准**：离线报告尾部清晰写明不支持或精度受限的高级计算列表。
