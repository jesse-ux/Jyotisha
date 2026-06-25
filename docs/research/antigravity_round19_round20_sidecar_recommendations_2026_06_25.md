# Antigravity AI 下一轮（Round 20）副手任务建议 (Round 19)

下一轮可继续指派给副手处理的 10 项高体量研究/只读任务：

1. **Asthakoot 36 分评判表常量构建**：从 VedAstro (MIT) 搬运并整理出 JSON 常量结构文件草稿，供主线代码引入。
2. **Asthakoot Oracle 对标方案**：在 `dasha_shadbala_oracle_cases.json` 同级建立 `ashtakoot_compatibility_cases.json`，设计它的校验字段。
3. **Playwright 冒烟脚本草稿**：编写 Node.js/Playwright E2E 脚本的初始草稿，包含打开 `http://127.0.0.1:5173` 并断言 `.oracle-evidence-progress-bar` 的逻辑。
4. **Shadbala 校验器升级逻辑撰写**：研究 `oracle_evidence_validator.py`，写出一段只允许 float 且 >=0 的 `_validate_shadbala_rupa` 函数供 Codex 参考。
5. **Prompt Pack 数据源联调审计**：验证 API 返回的 payload 是否成功嵌上了 `valid_packets: 0`。
6. **Vimshottari 精度下钻**：审查本地引擎 Dasha 算法与 PyJHora 的时分秒差异。
7. **Panchanga 开源组件剥离设计**：研究 `panchanga` (MIT) 中 Tithi 的日出偏移量，做个最简的复刻计划。
8. **Raman Ayanamsa 测试用例编写**：补充纯粹用于断言 Raman 落点差值的测试脚本草稿。
9. **UI 多语言术语映射表**：整理 50 个核心占星术语的中英文与梵文（如 sthana -> 位置力量），形成词典 JSON 草稿。
10. **Tauri 桌面端 Preflight**：继续深入调研 Tauri 在 macOS 上的代码签名（Code Signing）限制。

**落地建议**：这些体力活和长篇大论的代码设计继续全盘甩给副手，Codex 只负责最精简、最一针见血的核心代码注入。
