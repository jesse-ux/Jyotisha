# Antigravity AI Ayanamsa / ephemeris 精度差距 (Round 29)

## 岁差之争的绝对度数

| 测试维度 | 容差目标 | 当前情况 | 改进路径 |
|---|---|---|---|
| **Lahiri 对齐 JHora** | 0.001度 | `True` | 我们底层走 Swisseph，主轴准确。 |
| **Raman (拉曼)** | 0.005度 | 未实测 | 需从 API 支持透传 Ayanamsa 配置值，并在常量表里维护 Raman 差值。 |
| **KP (Krishnamurti)** | 0.005度 | 未实测 | KP 学派的基准线截然不同，它影响着 249 个 Sublord 的分割。必须实装！ |
| **Pushya Paksha** | 0.005度 | 缺失 | 补充参数支持。 |
| **夏令时历史黑洞** | 完全不错乱 | `部分失败` | 名人库里 1984 年加州的 Katy Perry 和 1964 年的案例，因夏令时 (DST) 切换问题跑出了错误的度数甚至宫位。这需要更健壮的 `pytz` 解析规则。 |

## 状态
`部分成立`
