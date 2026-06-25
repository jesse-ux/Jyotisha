# Antigravity AI VedAstro/MIT 可复制资产清单 (Round 28)

## 资产清单

| 资产名称 / 路径参考 | License 状态 | 目标转换位置 | 风险提示与不可复制项 |
|---|---|---|---|
| Ashtakoot 8 矩阵常数表 | 🟢 MIT | `scripts/ashtakoot_constants.py` | 直接抄写矩阵字面量，禁止复制其 C# 遍历逻辑。 |
| Panchang 节日计算规则 | 🟢 MIT | `scripts/panchanga_festivals.py` | 提取其判断 Tithi/太阳位置的常量，不要抄它的 API Controller。 |
| 各种 Ayanamsa 的微调度数 | 🟢 MIT | `scripts/ayanamsa_constants.py` | 我们底层用 swisseph，只需复用它的差值配置思路。 |
| 行星自然吉凶常量表 | 🟢 MIT | `scripts/planet_constants.py` | 提取数组字典。 |
| API 路由与参数命名风格 | 🟢 MIT | 脑内吸收 | 借鉴其 RESTful 风格，如 `/api/Calculate/Ashtakoot`。 |
| 界面组件 (若参考 RoxyAPI) | 🟢 MIT | `jyotish-app/` | 可以抄 HTML/CSS 布局，不要抄其 React Hooks 逻辑，我们是 Vanilla JS。 |

## NOTICE 要求
在项目根目录的 `NOTICE.md` 中必须增加：
```text
Portions of the astrological constant matrices are derived from VedAstro.
VedAstro is licensed under the MIT License.
Copyright (c) 2023 VedAstro
```

## 状态
`已成立`
