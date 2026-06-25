# Antigravity AI GraphQL 重构与瘦身路线 (Round 29 Extra)

## Payload 爆炸问题
目前的 `/api/chart` 接口每次都会全量吐出 D1-D60 所有分盘、几十种大运树的全部节点。
这个 JSON 高达好几 MB，不仅费服务器带宽，在手机端解析也会导致明显卡顿。

## 改进路线
1. **按需加载 (GraphQL 范式)**：虽然我们用 REST，但可以用参数控制。比如 `/api/chart?fields=d1,shadbala,dasha_level1`。
2. **独立拆分 Endpoint**：将 `Ashtakavarga` 和 `Dasha` 从主接口里剥离，前端点击 Tab 时再去拉取这部分数据。
3. 压缩浮点数精度，从小数点后 16 位压缩到后 4 位，足以。

## 状态
`未成立`
