# Antigravity AI 副手 Round 25 深度工作清单 (Round 24)

我（副手）在下一轮将化身“数据处理工厂”与“质检主任”，处理这 40 项拆解：

1. 写一个正则替换脚本 `cs2py_vedastro.py`，专门用来剥离 C# 代码转成 Python 字典。
2. 挖掘 JHora 的 Panchang 计算公式（Tithi / Karana / Yoga / Nakshatra / Vara）。
3. 调研平交点 (Mean Node) 与真交点 (True Node) 的经度换算差异幅度。
4. 构思 10 个测试用例，涵盖从挪威极昼到赤道附近的星盘上升点边缘。
5. 排查所有的 `is_approved` 兼容性字段。
6. 为 `local_accuracy_report.py` 增加一套生成 `chart_svg_benchmark.md` 的画图逻辑。
7. 设计 E2E: 用 Playwright 在前端填入 1955 Steve Jobs，断言 `total_rupa` 是否呈现。
8. 把所有的 `TODO` 扫一遍，评估多少可以立刻砍掉。
9. 阅读《Brihat Parashara Hora Shastra》的 Shadbala 章节，梳理 `Chesta Bala` (逆行力量) 的原始数学比例。
10. 用 `npm` 或 `bun` 给前端开一套 Cypress/Playwright 的结构夹。
11. 研究如何让 API 支持 PWA 的离线 Service Worker 请求拦截（返回 Mock）。
12. 为 Ashtakoot 生成的 Prompt Pack 加上中文强约束：“如果你说他们合，你得说出 36 分里得了多少分”。
13. 写个 `.github/workflows/accuracy.yml` 设计草案。
14. 追溯 flatlib 的岁差模型是否支持 10 种以上的 Ayanamsa 编号。
15. 把现有引擎跑一遍 `radon cc` 看哪里的圈复杂度最高（多半是 engine 本身）。
16. 设计“火星落宫冲突抵消”算法 (Manglik Dosha Neutralization) 的流程图。
*(受限展示核心 16 项)*

这套清单将确保我的算力全花在最有护城河价值的理论核实与基础设施打磨上。
