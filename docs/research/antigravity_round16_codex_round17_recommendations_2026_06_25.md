# Antigravity AI 给 Codex 的 Round 17 任务建议 (Round 16)

为了真正把 0/5 的收集瓶颈打破，并将 Shadbala 力量细粒度化，建议在下一轮优先执行以下 5 项实操任务：

## 1. 将 Artifacts 存档规范接入代码与文案
- **文件路径**：`references/oracle/artifacts/README.md`, `jyotish-app/main.js`
- **测试命令**：`git status`
- **验收标准**：目录已存在，且网页上在下载 Evidence 包时，能提示用户需打码并在包里写入规范的相对路径。
- **人工提供外部截图**：否，纯文本/代码操作。

## 2. 将 Shadbala 六分量强校验打入底层门神
- **文件路径**：`scripts/oracle_evidence_validator.py`
- **测试命令**：`pytest tests/test_oracle_evidence_validator.py`
- **验收标准**：当 `targetFields` 有 `shadbala_components` 且缺失 `sthana` 等键时，返回红灯。
- **人工提供外部截图**：否，纯代码防线。

## 3. 生成第一条 `template_user_REDACTED_YEAR` 的 JHora 样本指南
- **文件路径**：`docs/user_jhora_capture_guide.md`
- **测试命令**：无
- **验收标准**：将本轮报告 C 中的输入项与要求转化为一份能公开发布的 markdown 教程。
- **人工提供外部截图**：否，这是纯文本撰写。

## 4. 增加 Dasha/Shadbala 真实进度仪表盘
- **文件路径**：`jyotish-app/main.js`, `jyotish-app/style.css`
- **测试命令**：`npm run build --prefix jyotish-app`
- **验收标准**：在 `renderOracleEvidenceIntakePanel` 的头部渲染出本轮报告 D 中设计的进度条或表格。
- **人工提供外部截图**：否。

## 5. 亲手录入第一个跑通链路的截图和 JSON！
- **文件路径**：`references/oracle/artifacts/jhora_REDACTED_YEAR_moon_lahiri_v1.png` 以及修改 `references/oracle/dasha_shadbala_oracle_cases.json`
- **测试命令**：`python3 scripts/oracle_evidence_validator.py --queue-file references/oracle/dasha_shadbala_oracle_cases.json`
- **验收标准**：`valid_packets: 1` 历史性破零。
- **人工提供外部截图**：**是！** 这是最难的一步，要求 Codex（或操作者）真的去开个虚拟机截图，并把图片妥善归档，把 JSON 填满晋级。
