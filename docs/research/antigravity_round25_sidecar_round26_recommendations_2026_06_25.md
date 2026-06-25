# Antigravity AI 副手 Round 26 继续实施任务建议 (Round 25)

下一轮我（副手）将接手这些无需更改源码但极其繁重的数据核对与调研：

1. 写个脚本，将 VedAstro 的 27x27 Nadi 分数二维数组全自动抠出来，转成 Python JSON。
2. 挖掘 BPHS 中针对“巨蟹座火星落 7 宫”的 Kuja Dosha (火星煞) 豁免古文例外表。
3. 把我们找出的所有 13 种未显示的 Varga（比如 D3, D10）的梵文名字和英文含义做个字典。
4. 构思 `/api/panchang` 返回结构：应该带上日出日落时间和 Rahu Kalam 凶时。
5. 设计针对 AstroSage 合盘结果的 Playwright 爬虫（如果有验证码则罢休），为了自动化对比。
6. 继续查阅 flatlib 的底座，看看它对除 Lahiri 外的 Ayanamsa（比如 Raman）的误差。
7. 在 Github Actions yaml 文件里构想一个 `accuracy.yml`。
8. 设计一套用 Cypress 对前端 Vue 进行 12 种不同极端经纬度的表单填写压力测试。
9. 给 JHora 的 5 种不同交点计算方式（True Node vs Mean Node）做个图表。
10. 把 `local_accuracy_report.py` 吐出的 JSON 进行数据可视化（利用 mermaid.js 饼图）。
*(精简至 Top 10)*

只要我不碰主线代码，我就是项目的一块“测试铁砧”！
