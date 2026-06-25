# Antigravity AI 外部 oracle 精度闭环路线 (Round 29)

## 人类与机器配合战

我们要把“算得准不准”从开发者的嘴硬，变成铁证如山。

1. **收集 50 份命盘（人类）**：名人库 + 各种夏令时边界案例的日期经纬度。
2. **喂给 JHora/AstroSage（人类）**：手工跑出它们的 Dasha 交接时间、Shadbala 的 Rupa 浮点数、Ashtakoot 的 36 项总分。
3. **填写 `oracle_cases.json`（人类）**：把靶标数据填进去。
4. **运行 `oracle_evidence_validator.py`（机器）**：系统自动跑本地算法，如果和靶标误差大于 1% 或 2 天，直接标红阻断。

## 闭环缺口
我们现在有了框架（JSON 和 Validator），但里面的靶标值全是 0 或空着。必须让人类先停下写代码，去截图填数字。

## 状态
`需要人工外部工具`
