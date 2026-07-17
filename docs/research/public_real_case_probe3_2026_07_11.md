# 3 个独立公开案例补充检测（2026-07-11）

## 设计

沿用冻结 V2，不修改阈值、不先看星盘选人。三案全部为 Astro-Databank Rodden AA，且与前 20 人不重复：

| 人物 | 领域 | 公开事件 | 来源 |
|---|---|---|---|
| Donald Trump | career/public power | 2017-01-20 就任美国总统 | [美国国会就职委员会](https://www.inaugural.senate.gov/58th-inaugural-ceremonies/) |
| Leonardo DiCaprio | career/award | 2016-02-28 获奥斯卡最佳男主角 | [Academy Awards](https://www.oscars.org/oscars/ceremonies/2016) |
| Meghan Markle | legal marriage | 2018-05-19 与 Prince Harry 结婚 | [The Royal Family](https://www.royal.uk/wedding-duke-and-duchess-sussex) |

出生资料逐案保存在 `references/real_case_calibration/replay_manifest_probe3_v2.json`。

## 结果

| 人物 | 分数 | 判定 | 主要命中证据 |
|---|---:|---|---|
| Donald Trump | 3 | miss | Narayana lord 事业宫关联；Double Transit strong |
| Leonardo DiCaprio | 1 | miss | Jupiter 落事业事件宫 6 |
| Meghan Markle | 7 | strong_hit | Jupiter 婚姻 karaka；Saturn 为 7L；D9 7L；Double Transit strong |

补充样本：`1 strong + 0 weak + 2 miss`，正事件激活召回和精确标签率均为 `1/3`。样本太小，不能据此晋级或降级规则，但必须作为 V2 泛化反证公开。

合并 23 案例后：

- 总体：`9 strong + 8 weak + 6 miss`，正事件激活召回 `17/23 = 0.7391`，精确标签率 `9/23 = 0.3913`。
- 事业：`8/12 = 0.6667` 激活召回，`4/12 = 0.3333` 精确标签率。
- 婚姻：`9/11 = 0.8182` 激活召回，`5/11 = 0.4545` 精确标签率。
- balanced accuracy 仍 blocked：没有负事件控制样本。

## 新发现

1. 事业缺口不只限政治身份。DiCaprio 的明确奖项事件同样漏判，说明当前 D10/A10 层只检查活动大运星是否等于上升主、10L、AmK 或落 10 宫，覆盖不足。
2. Trump 的 Jupiter/Jupiter 与强双重过境仍未跨阈值，证明通用宫位加分不能替代 D10 Raja Yoga、行星相位、AL-A10、年度盘及公众权力专项裁决。
3. Meghan 的婚姻事件完整命中，支持现有 D1 功能宫主 + D9 7L + karaka + Double Transit 的婚姻组合，但单案不能证明整体准确率。
4. 不应按这三案立即新增分数。下一步应先冻结 V3 候选：D10 宫主相位/Raja Yoga、Narayana AD/PD、Varshaphala；再用新的至少 10 案例验证。

机器报告：

- `docs/benchmark/public_real_case_probe3_v2_2026_07_11.json`
- `docs/benchmark/public_real_case_23_case_observation_2026_07_11.json`

边界：全部是正事件回放，不是科学预测准确率；VedAstro official raw 与三引擎 parity 未因此闭环。
