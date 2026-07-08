# Antigravity AI 给 Codex 的 Round 12 任务建议 (Round 11)

经过全面复核与差距审视，以下为给 Codex 派发的 Round 12 核心执行队列，重点向着真正的产品易用性开火。

## 任务 1：将校准状态下发至“离线图表导出”
- **执行路径**：修改 `jyotish-app/jyotish-export-modules.js` 或相关的落盘/截图导出函数。
- **动作**：确保在导出生成的 PNG 图像或 HTML 档案尾部，强行烙印一段文本：“Dasha/Shadbala Calibration Status: ready_for_calibration: 0。起步大运未达绝对校验基准，请以此为参考。”
- **验收命令**：无专属，但在真实浏览器下测试导出产物，确认离线文件带有边界声明。

## 任务 2：制作“外部真值投喂”前端表单
- **执行路径**：在 `jyotish-app/` 增加一个诸如 `oracle-contribute.html` 或对应子视图面板。
- **动作**：对接目前的 `references/oracle/dasha_shadbala_oracle_cases.json` 模板任务，提供 5 个可视化的悬赏卡片。每个卡片允许极客占星师们阅读所需的输入占星条件，并上传截图 + 填写真值。
- **验收命令**：`npm run build --prefix jyotish-app`，并且人工验证 UI。

## 任务 3：录入首批 JHora 真实截图数据
- **执行路径**：人工脱离自动化系统操作。
- **动作**：在一台干净且无 GPL 污染的独立机器上，启动闭源 JHora。按照 `dasha_shadbala_oracle_cases.json` 中的 `template_steve_jobs_dasha_lahiri` 与 `template_synthetic_north_china_shadbala_raman` 参数排盘。将得到的截图作为 Artifact 存入系统，并将读数写入 JSON 靶标。
- **验收命令**：
  ```bash
  python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format json > /tmp/queue.json
  python3 scripts/oracle_evidence_validator.py --queue-file /tmp/queue.json
  ```
  **验收标准**：`valid_packets` 从 0 突破至 2。

## 任务 4：一键产品化包装探路
- **执行路径**：评估 Tauri 或 Pake 的打包方案。
- **动作**：为项目新增一个极简启动指引或跨平台的壳子配置脚本，使得哪怕不知道什么是 npm 和 python env 的用户，也能一键启动我们的 Web 服务。
- **验收标准**：文档化验证流程，并提供给普通用户下载的制品入口。
