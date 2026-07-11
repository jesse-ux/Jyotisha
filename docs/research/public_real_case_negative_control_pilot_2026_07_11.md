# 真实案例负样本日期排序 Pilot（2026-07-11）

## 设计

对 Trump 就职、DiCaprio 奥斯卡、Markle 婚姻三个 AA 案例，分别取真实事件日前后 `30/60/90/120` 天，共 8 个控制日期。控制日期只保证没有发生该项精确目标事件，不保证没有其他人生事件。

统一使用 V2.1；SAV/BAV 仍为非评分证据。并列采用保守排名：控制日期与真实日期同分时，控制日期排在真实日期前。

## 汇总

- 真实日期 Top-1：`0/3`。
- 真实日期 Top-3：`0/3`。
- Mean Reciprocal Rank：`0.1407`。
- 平均真实日分数边际：`-1.3333`。
- 24 个控制日期中，`10/24 = 41.67%` 达到 activation 阈值。
- `10/24 = 41.67%` 达到 strong 阈值。

## 逐案

| 案例 | 真实分 | 最高控制分 | 真实日排名/9 | 结论 |
|---|---:|---:|---:|---|
| Trump 2017 就职 | 3 | 7 | 5 | 两个更早控制日期反而 strong |
| DiCaprio 2016 奥斯卡 | 1 | 1 | 9 | 九个日期全部同分，完全无日期区分力 |
| Markle 2018 婚姻 | 7 | 7 | 9 | 真实日和八个控制日期全部 strong |

## 裁决

当前评分器主要识别持续数月或更长的 Dasha、分盘与慢行星背景，不能从该背景中确定具体月日。进一步使用 `±1年/±2年` 的 12 个年度控制日期后，真实日 Top-1/Top-3 也只有 `33.33%`：Trump、DiCaprio 均排最后，只有 Markle 婚姻排第一。

由此新增硬门：

- `exact_day`：blocked。
- `exact_month_from_current_replay_score`：blocked。
- 当前最大支持精度：`unvalidated_broad_window`。
- 事业 timing：blocked。
- 婚姻宽窗口：partial candidate，仍需更多样本。

月级或日级输出只有在 PD/PrAD、Mudda/Varshaphala、精确 KP cusp、快速过境加入后，并在新的控制日期排名中通过，才能解除门控。

本 pilot 仍不能计算完整 balanced accuracy，因为控制日期未被独立核验为“所有同领域事件均未发生”。但它足以反证当前分数具有精确日期识别能力。

机器报告：

- `docs/benchmark/public_real_case_negative_control_pilot_2026_07_11.json`
- `docs/benchmark/public_real_case_annual_control_pilot_2026_07_11.json`
