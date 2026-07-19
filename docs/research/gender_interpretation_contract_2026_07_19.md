# Gender interpretation contract — 2026-07-19

本合同只管解释层；不改变星盘计算。

## 总原则

- 性别不改变 D1、分盘、Dasha、Shadbala、Ashtakavarga、Yoga、Ayanamsa、Node mode。
- 性别只能在婚恋/配偶/婚姻应期加权、生育语境表达里作为辅助层。
- 不能只靠“男金女木”下婚恋结论。

## 婚恋/配偶

基础栈性别中立：

- 7宫
- 7宫主
- D9
- UL
- Darakaraka

性别辅助层：

- 男命增强 Venus。
- 女命增强 Jupiter/Mars。
- `nonbinary`、`prefer_not_to_say` 或缺失时，使用性别中立栈，不强行套二元规则。

## 婚姻应期

基础仍需：

- 7宫主周期
- D9 激活
- UL 激活
- DK 周期
- Vimshottari + Narayana 交叉

性别只能增加权重：

- 男命：Venus 周期/过境激活可作为补充证据。
- 女命：Jupiter/Mars 周期/过境激活可作为补充证据。

禁止说：只因某个性别象征星激活，所以应期已验证。

## 子女/生育语境

基础仍是：

- 5宫
- 5宫主
- Jupiter
- D7
- Putrakaraka

性别只用于语言和现实语境；不得给医疗、生育、怀孕保证结论。

## 产品字段建议

```ts
gender: "male" | "female" | "nonbinary" | "prefer_not_to_say" | null
```

文案建议：

> 该信息仅用于传统婚恋/配偶象征星的解释加权，不改变星盘计算。

## 产品回答边界

如果 gender 缺失，不阻塞回答。只在婚恋/配偶问题里可轻问：

> 如果你愿意，也可以补充性别；我会用传统配偶象征星再校正一次。

若使用 gender，必须说明它只是传统辅助象征层，不是唯一判断。
