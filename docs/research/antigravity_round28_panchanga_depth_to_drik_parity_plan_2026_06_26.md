# Antigravity AI Panchanga/Calendar 商业深度路线 (Round 28)

## 商业级日历缺口

| 模块 | 对标对象 | 当前缺口 | 实施路径 |
|---|---|---|---|
| **Vrata / 节食斋戒** | Drik Panchang | 无 | 算准 Ekadashi (第11/26 Tithi)，并在月历打上特殊标记。 |
| **Festival / 印度历节日** | AstroSage | 无 | 实现一个基于太阳和 Tithi 结合的节日匹配器，如 Diwali 判定。 |
| **Nitya Yoga** | Prokerala | API 有，缺展示 | 必须展示每天的 Yoga 是 Auspicious 还是 Inauspicious。 |
| **Karana** | Drik Panchang | API 有，缺展示 | 半个 Tithi，对特殊商业活动有用，需要前端展示。 |
| **Tara Bala** | AstroSage | 无 | 根据用户出生 Nakshatra 与当日 Nakshatra 计算个人化的吉凶 (1-9)。 |
| **Chandra Bala** | AstroSage | 无 | 月亮落在用户本命月亮起算的第几宫，决定情绪吉凶。 |
| **Pancha Pakshi** | Tamil历 | 未登记新技法 | 泰米尔地区的五鸟测时法，这是一个杀手级特性。 |
| **Gowri Panchangam** | 南印历 | 未登记新技法 | 另一种分时吉凶（Nalla Neram）。 |
| **ICS 订阅** | Google Calendar | 极度匮乏 | 将以上的吉日和 Rahu Kala 封装成 `.ics` 流。 |
| **UI 呈现** | Hora Prakash | 仅有裸 JSON | 在前端增加一个月历组件（`jyotish-app/main.js`）。 |

## 状态
`已成立`
