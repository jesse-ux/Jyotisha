# Antigravity AI Artifacts 存档规范修复后黑盒复核 (Round 17)

## 1. 对标
在正规的开源项目中，若涉及用户提交的截图及隐私证据，必须有透明的合规指引。我们的设计是依赖 `references/oracle/artifacts/` 作为外部截图的隔离带，由 `README.md` 进行打码与文件类型规范。

## 2. 开源参考
该任务原本要求 Codex 在本轮创建 `references/oracle/artifacts/README.md`，并在其中写入隐私保护条款，同时要求网页端在导出 Evidence Packet 模板时提示截图相对路径的写法。

## 3. Bug
本轮执行黑盒复核时发现：Codex 依然**未执行**这部分的修复。
- **检查点 1**：`references/oracle/artifacts/README.md` 是否存在？**否**。
- **检查点 2**：Evidence Packet 下载文案是否提示 `source_artifact` 写相对路径？**否**。
- **检查点 3**：是否明确要求私人截图必须打码？**否**。
- **检查点 4**：是否禁止私人 PDF 原件、浏览器 scratch 入库？**否**。
- **检查点 5**：公开名人或合成样本是否允许入库？**未定义**。
- **检查点 6**：测试脚本 `test_oracle_artifact_storage_policy_is_documented` 运行失败？**是**，提示找不到匹配的测试。
- **检查点 7**：命令行复现检索：`rg "references/oracle/artifacts" references/oracle` 为空。
- **检查点 8**：结论状态：**未成立**。

**修复建议**：Codex 应当立即在 `references/oracle/` 下执行 `mkdir artifacts`，并生成 `README.md` 写入打码红线，同时在 `jyotish-app/main.js` 中把下载提示加上。

*(此测试无须人工截图介入)*
