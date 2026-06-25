# Antigravity AI 给 Codex 的 Round 13 任务建议 (Round 12)

在打通了所有的透明度屏障后，我们的基础生态防线已宣告竣工。以下是向着“易用性爆发”和“真值录入破冰”进发的执行指令：

## 1. Web 增设 Oracle 表单原型
- **文件**：`jyotish-app/oracle-intake.html` (或纳入 `main.js` 面板)
- **目标**：将 JSON 模板做成面向普通志愿者的只读与本地提交交互表单。
- **验收**：执行 `npm run build --prefix jyotish-app`，在浏览器打开发现有一个用于真值截图收集的入口，表单项完全覆盖 Round 12 规划。

## 2. Evidence Packet 下载通道
- **文件**：`jyotish-app/api-bridge.js` 和 `scripts/oracle_collection_queue.py`
- **目标**：为了方便极客手工填表，在页面提供一键下载单个任务对应的空白 `draft` JSON 模板的功能。
- **验收**：生成的 JSON 完全吻合 `evidence validator` 的 schema 校验。

## 3. 表单/模板导入并执行黑盒验证
- **文件**：新增入口，允许用户通过页面或 CLI 注入填好截图及靶向数值的证据包。
- **目标**：调用底层的 `oracle_evidence_validator.py` 并实时显示绿灯/红灯（缺失某个 metadata 或 target 空白）。
- **验收**：人工构造一个错误的包丢进验证器，确保能输出 `problems` 清单。

## 4. 移动端/小屏视图边界自适应检查
- **文件**：`jyotish-app/style.css`
- **目标**：真实浏览器或真机模拟环境下，确保带有一大堆描述文案的 Trust Center 面板与离线长图导出，不会产生截断、折行丑陋或滚动条溢出。
- **验收**：Chrome 开发者工具切换到 iPhone SE 尺寸，核验无排版灾难。

## 5. 打包启动的终极极简化
- **文件**：`start_jyotish.sh` 或 Tauri 脚手架
- **目标**：不要再让用户分别敲击两三次命令，把 Python 虚拟环境与前端服务裹在一条指令或一个二进制包里。
- **验收**：纯净 Mac/Windows 环境下的双击即可使用。
