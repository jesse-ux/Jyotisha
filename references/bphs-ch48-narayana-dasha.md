# BPHS Chapter 48 – Narayana Dasha

## 概述

Narayana Dasha（亦作 Rishi Dasha / Padakrama Dasha）是 Parasara 体系中的另一种大运系统，
以 Lagna 为起点，按黄道十二星座顺序推进，每个星座的大运长度取决于该星座的守护星
到该星座的"步数"。

## 计算方法（PVN Rao / BPHS Ch.48 传统算法）

1. 从 Lagna 所在星座开始
2. 按黄道顺序（白羊→金牛→双子→...→双鱼）遍历 12 星座
3. 每个星座的大运年数 = 该星座守护星所在星座到该星座的"步数"
   - 例如：Lagna 在白羊，白羊守护星 Mars 在巨蟹 = 4 步 → 白羊大运 4 年

## 当前实现状态

当前 `scripts/narayana_dasha.py` 实现了基础算法，覆盖：
- Lagna 起运
- 黄道序 12 星座推进
- 守护星步数计算

## 局限

- 未完整覆盖 BPHS Ch.48 所有变体
- 未与 PyJHora Narayana Dasha 做基准比对
- 当前标注为 **covered**，待 benchmark 后确认

## 参考

- BPHS Chapter 48 (Rao 英译)
- PyJHora Narayana Dasha 输出
- PVN Rao "Dasa Systems in Hindu Astrology"
