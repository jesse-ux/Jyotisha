# Antigravity AI 外部校准透明度 Bug 报告 (Round 9)

## 文件级 Bug 清单

本部分枚举直接影响“普通用户如何看待系统准确度”的产品化缺陷。

| 严重程度 | 文件路径 | 行号 | 现象 | 用户影响 | 修复建议 |
|---|---|---:|---|---|---|
| **P0** | `jyotish-app/index.html` <br/> `jyotish-app/main.js` | 全局 | Web 前端完全没有显示后台极为严谨的 `ready_for_calibration` 与 `valid_packets` 等外部采源大盘进度数据。 | 普通用户在使用 Dasha 时，可能误认为人生重大起步日期是100%绝对校准的。 | 在网页显眼处（如首屏底部或专属 Trust Center 弹窗）动态读取或静态写明当前 Dasha/Shadbala 的校准队列进展。 |
| **P1** | `jyotish-app/ai-chat.js` <br/> `jyotish-app/skill-map.js` | 全局 | AI Chat 系统没有在 Prompt 的底层结构中把 `external_verified` 尚未完成的状态强行注入上下文。 | 若用户直接问大模型“我的这几年大运精确到了哪一天？”，大模型可能会脱离界限进行幻觉性肯定回答。 | 在请求大模型生成洞察时，强行在头部 System Prompt 附加一段关于“高级模型仍在收敛对齐阶段，只能做总体参考”的提示。 |
| **P2** | 整体产品部署架构 | - | 虽然与代码 Bug 无关，但当前的纯工程化入口（依赖 Python 和 Node 命令行）将一切没有代码知识的用户挡在门外。 | 用户只能去看静态 Demo（甚至有些后台高级功能调不出来），体会不到校准大盘的意义。 | 安排一次桌面环境的极简打包（如 Pake），一键拉起后端 API 服务器与前端壳。 |
