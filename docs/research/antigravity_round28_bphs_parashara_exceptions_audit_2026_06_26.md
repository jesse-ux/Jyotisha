# Antigravity AI BPHS (Brihat Parashara Hora Shastra) 例外规则审计 (Round 28)

## 古典文献的“反转”魅力
规则 1 是凶，加上条件 A 就变成了吉。我们的 `yoga_rules.json` 目前只支持硬性 AND/OR。

## 审计点
1. **Neecha Bhanga Raja Yoga (落陷反转)**：当一颗星星衰弱，但其定位星处于角宫，或者伴随耀升的星星，衰弱取消变大吉。
2. **Kendradhipati Dosha**：吉星（木、金）成为角宫的主星时，失去其吉性。
3. **Badhaka (阻碍者)**：不同上升点有其专门的阻碍宫位（活动宫对应 11 宫，固定宫对应 9 宫等）。
4. 本次需排查我们的代码中有没有处理以上例外。目前看：**均未处理**。

## 状态
`未成立`
