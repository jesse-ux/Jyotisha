# Antigravity AI 整机碎片复用第二轮 (Round 29)

## 本地死角再探

在我们过往跑的 Benchmark 和 `references/open_source_sources/` 文件夹中，还有这些可以被榨干的油水：

1. **`dashaflow` (MIT)**：里面其实有完整的 `muhurta.py` 和 `dignity.py` 逻辑。我们现在自己重写了一套简陋版的 Muhurta，不如直接照抄它的评分常数。
2. **`jyotishganit` (MIT)**：这里面有个巨大的 `constants.py`，里面写死了 `ATHIMITRA: 22.5` 这种精确的小数。这正是我们计算 Shadbala 时极度缺乏的魔法常数。
3. **`jaimini-tropical` (MIT)**：虽然名字带 tropical，但它对 Chara Dasha 和 Padas 的抽象极度精妙。可以借鉴它对宫位跳跃的计算树。
4. **`panchanga_api` (MIT)**：里头有个 Tithi 端点和太阳差值计算工具，可以校准我们的算法误差。

## 状态
`已成立`
