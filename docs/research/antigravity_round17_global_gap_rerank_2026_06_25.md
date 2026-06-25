# Antigravity AI 全局同品类差距重排 (Round 17)

随着架构深入，我们重新对标行业内的顶级软件，找出核心痛点差距：

| 排名 | 能力 | 当前状态 | 对标对象 | 为什么重要 | Codex 下一步 |
|---|---|---|---|---|---|
| 1 | Oracle/accuracy workflow | 半成品 (仅 API 侧跑通) | 所有开源及商业项目 | 确立“真值”标杆的基础，是我们的最大卖点。 | 在网页展示进度面板，完成首个 JHora 样本真实跑通。 |
| 2 | PWA/static demo 边界 | ✅ 已确立 | Web 占星产品 | 防止用户在静态无后端的情况下迷失。 | 无。已通过文案静态界定。 |
| 3 | AI Prompt Pack/RAG 用户端承载 | ✅ 已确立 | 类似 AI 星盘助手 | 将复杂计算打包供大模型消耗，降低幻觉。 | 无。已提供一键复制 `jyotish_engine.py` 输出结构。 |
| 4 | Shadbala absolute calibration | 🚧 0/4 | JHora | 行星力量是进阶核心。 | `oracle_evidence_validator.py` 中写死六分项检查。 |
| 5 | Dasha boundary calibration | 🚧 0/3 | JHora / PyJHora | 人生大运起运时间差之毫厘谬以千里。 | 在样本收集时强制规定 Ayanamsa 和年长参数。 |
| 6 | Ashtakoot 合婚样本 | 🔴 缺失 | VedAstro / 婚恋 APP | 最强烈的商业与大众痛点需求。 | 编写 36 分评级算法并通过 JHora 找盘核对。 |
| 7 | KP Horary 样本 | 🔴 缺失 | 专用 KP 商业软件 | 职业高手的短期精准预测武器。 | 需要实现极高精度的时辰划分（1-249）。 |
| 8 | Muhurta 搜索样本 | 🔴 缺失 | JHora | 择吉日需求旺盛。 | 需要处理多维度的 Tara/Chandrabala 重叠评价体系。 |
| 9 | Bhava Chalit/Sripati/Placidus 样本 | 🔴 缺失 | PyJHora / JHora | 宫位划分争议极大，影响星曜落宫判定。 | 提供高纬度（极地）的压力测试用例。 |
| 10 | D24/D30/D60 深分盘样本 | 🔴 缺失 | JHora | 微观命运分析。 | 仅限收集带 BTR 校验名人的极致用例。 |
