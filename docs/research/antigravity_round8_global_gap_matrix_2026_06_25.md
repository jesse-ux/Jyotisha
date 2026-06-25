# Antigravity AI 全球标杆产品差距矩阵 (Round 8)

## 核心对标差距速览

通过横向查阅相关公开技术档案与架构形态，目前本项目在传统算法广度和绝对值精度上距离头部产品仍有可见距离。

| 对标对象 | 强项 | 我们当前对应文件/功能 | 仍缺什么 | 建议优先级 | 不可复制/许可证边界 |
|---|---|---|---|---|---|
| **VedAstro (API)** | 提供高达 `596+` 种繁浩的计算方法；内置 Koota 合婚匹配；庞大的 Panchanga（择吉黄历）；面向全球的大型 API 与 AI Chat 对接文档。 | `jyotish_api_server.py`, `full-reading.ai_prompt_pack`, `jyotish-app/*` | 缺少直接可用的 API 文档供第三方对接；缺少 Ashtakoot (合婚评分) 和详尽的 Panchanga 吉凶历法事件。 | **P2** (在核心框架稳固后扩充) | MIT 许可证较为宽松，允许借鉴思路甚至融合其开放的数据接口结构，但尽量避免直接照搬造成强依赖。 |
| **PyJHora** | 彻底深耕 Python 占星计算生态。包含天量的 Dasha 流派算法、分盘变种及 Shadbala 等绝对力量分项计算，还原度极高，内置海量传统常数查表。 | `scripts/shadbala.py`, `scripts/dasha_calculator_enhanced.py` | 缺失如 Chara, Yogini 外更多大运系统；缺失 Shadbala 更高颗粒度展开（如 Vimsopaka 等极微弱力量点）；常数的精微调教。 | **P1/P2** (看具体模块急迫性) | **AGPL-3.0 红色警告**。绝对不可照抄其代码、复制其常量表。只能提取其跑出的 `stdout` 最终计算值作为黑盒测试靶标进行对齐。 |
| **Jagannatha Hora (JHora)** | 印度占星桌面软件的“教皇”级存在。包含数以百计的传统设置项（从计算节点、岁差开关到特殊经纬度修正），被全球顶尖占星师奉为准绳。 | `references/oracle/dasha_shadbala_oracle_cases.json`, `scripts/oracle_collection_queue.py` 等整个质量门体系。 | 我们的大运（Vimshottari Dasha）交接日与星体力量（Shadbala）最终绝对值尚未经历海量样本的验证对标，底层开关不够丰富。 | **P1** (最优先) | 闭源免费商业软件。无法调用 API 或阅读源码，**只能依靠人工键盘录入参数、肉眼截屏**的方式采集真值作为校准依据。 |
