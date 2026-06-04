# Muhurta Complete Guide

## 概述

Muhurta 是 Vedic 择时占星系统，核心目标是在正确的时间启动行动，
使事件结果最大化。Muhurta 分析基于 Panchanga 五要素。

## Panchanga 五要素

| 要素 | 含义 |
|---|---|
| Tithi | 月相日（月亮相对于太阳的角度，1-15） |
| Vara | 曜日（周日=太阳，周一=月亮，...） |
| Nakshatra | 月亮所在星宿（27 宿） |
| Yoga | 日月合相特殊组合（27 种） |
| Karana | 半 Tithi（11 种） |

## 其他要素

- **Hora**：昼/夜由太阳/土星守护的时段
- **Abhijit**：中天最吉时刻（非所有日都存在）

## 活动适宜性判断

核心原则：
1. Rasi / Nakshatra 与活动性质的匹配
2. 避开 Kemadruma / Rikta Tithi
3. 检查 Vara / Hora 守护星强度
4. 避开恶性 Yoga（如 Vaidhriti）

## 当前实现状态

`scripts/muhurta.py` v6.0.21 实现：
- Panchanga 五要素计算
- Hora / Abhijit 计算
- 5 类活动适宜性检查
- `--scan-days` 多日扫描

## 局限

- 未覆盖所有 20+ 传统活动类型
- 部分禁忌规则简化
- 未与经典 Muhurta 表（如 Muhurta Chintamani）做完整 benchmark

当前标注：**covered**，待更多活动类型补充后升级。

## 参考

- "Muhurta Chintamani" (Sage Narada)
- "Essentials of Muhurta" (Sanjay Rath)
- PyJHora Muhurta 模块
