# Antigravity AI 给 Codex 的 Round 16 任务建议 (Round 15)

目前的准确率大动脉已经铺开，只缺血液流动。请 Codex 优先切入证据截图库与物理存档环节，随后发起对高级技法的攻坚：

## 1. 建立 Artifacts 本地存档池
- **文件路径**：创建 `references/oracle/artifacts/` 目录以及其中的 `.gitkeep` 和 `README.md`。
- **测试命令**：`ls -la references/oracle/artifacts/`
- **验收标准**：目录存在且有明文规范声明：凡包含全名生辰截图须打码，纯净参数截图方可提交。
- **人工**：不需要，纯代码操作。

## 2. 增加 Evidence Packet 后端落地保存能力
- **文件路径**：`scripts/jyotish_api_server.py`
- **动作**：当 Web 前端通过 `/api/oracle_evidence` 上传 Draft Json 并通过本地 validator 查验（亮绿灯）后，提供一个保存包文件至本地特定缓冲目录（如 `references/oracle/inbox/`）的选项。
- **验收标准**：上传一个合格的包，能在本地磁盘发现此文件的物理拷贝。
- **人工**：不需要。

## 3. 手工获取历史性破冰样本
- **文件路径**：`references/oracle/artifacts/` 和 `references/oracle/dasha_shadbala_oracle_cases.json`
- **动作**：别再写码了。人工打开 JHora，填入 Steve Jobs 的 1955-02-24 参数，截图。然后人肉把这张截图放到 artifacts 里，用编辑器手写 JSON，保存，运行验证器。
- **测试命令**：`python3 scripts/oracle_evidence_validator.py --queue-file ...`
- **验收标准**：输出必须包含 `valid_packets: 1`。
- **人工**：**必须人工操作外部黑盒软件。**

## 4. 将 Shadbala 从占位升级为六项强制拦截
- **文件路径**：`scripts/oracle_evidence_validator.py`
- **动作**：对带有 `shadbala_components` 在 `targetFields` 中的 case，不仅检查该键存在，还要深入检查子键 `sthana`, `dig`, `kala`, `chesta`, `naisargika`, `drik` 的浮点数是否齐全。
- **测试命令**：用一个缺斤少两的 JSON 喂给 validator，必须报错。
- **验收标准**：残缺六分量包被准确抛出红灯问题。
- **人工**：不需要。

## 5. 高阶技法雷达矩阵同步至前端
- **文件路径**：`jyotish-app/main.js` (Trust Center 或新面板)
- **动作**：在网页里诚恳地列出 Ashtakoot, KP 等的高级列表，目前均标记为 `未覆盖/建设中`。
- **测试命令**：`npm run build --prefix jyotish-app` 并肉眼查看本地服务界面。
- **验收标准**：用户点击面板，立刻知道本程序不支持什么。
- **人工**：不需要。
