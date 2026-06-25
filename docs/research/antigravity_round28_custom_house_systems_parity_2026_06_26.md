# Antigravity AI 自定义宫位制 (House System) 对齐 (Round 28)

## 分系统对比
印度占星多数时候使用 **Whole Sign (等宫制 / 整个星座为一宫)**。但 KP 流派和部分古典流派强调 **Placidus** 或 **Sri Pati** 宫位系统。

## 检查点
1. 我们的引擎目前在 `jyotish_engine.py` 强绑定了 `Whole Sign`。
2. `/api/chart` Payload 必须支持传入 `house_system="placidus"`。
3. 在采用 Placidus 时，一个宫位里可能出现跨越两个星座的截夺现象，目前的展示 UI（那种正方形网格图）将无法表达这种截夺。
4. UI 修改：必须为 KP 等流派单独画圆形的宫位排布图，而不是传统的方块图。

## 状态
`部分成立`
