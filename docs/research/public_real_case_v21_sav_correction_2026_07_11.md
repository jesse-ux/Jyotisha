# 真实案例 V2.1 计分修正与 SAV/BAV 审计（2026-07-11）

## 修正内容

1. MD 与 AD 为同一颗星时，不再重复执行整套宫位、落宫和 karaka 加分。
2. 保留旧字段兼容，但新增真实指标名：
   - `known_event_activation_rate`
   - `strong_activation_rate`
3. `positive_event_recall` 与 `exact_label_rate` 标记为 deprecated。
4. 23 案例全部加入 D1 SAV/BAV、事件宫 SAV、事件日 Jupiter/Saturn 过境 SAV/BAV；本轮不参与评分。

## V2.1 观察结果

- 总体：`7 strong + 10 weak + 6 miss`。
- known-event activation：`17/23 = 0.7391`。
- strong activation：`7/23 = 0.3043`。
- 事业：activation `8/12 = 0.6667`，strong `2/12 = 0.1667`。
- 婚姻：activation `9/11 = 0.8182`，strong `5/11 = 0.4545`。

旧 23 案例 strong activation 为 `9/23 = 0.3913`。去重后降为 `7/23 = 0.3043`，确认重复 MD/AD 计分曾抬高强命中数量。

## SAV/BAV 描述性结果

| 分组 | 事件宫 SAV 均值 | Jupiter/Saturn 过境 SAV 均值 | 过境星自身 BAV 均值 |
|---|---:|---:|---:|
| 已激活 strong/weak | 28.809 | 28.735 | 3.882 |
| miss | 30.375 | 27.583 | 3.917 |

当前正样本中，miss 的事件宫 SAV 均值反而高于已激活组，过境 BAV 几乎没有差异。因此：

- SAV 不能直接作为“高分即发生事件”的加分器。
- SAV 更适合作为本命承载力背景，与大运、宫主、BAV 和过境共同分析。
- 是否具有日期区分能力，必须用同人物同年度负样本验证。

## 技术边界

- 本仓 SAV 总数和七曜 BAV 总数不变量已由 `tests/test_ashtakavarga_invariants.py` 守门。
- 本轮 23/23 案例 SAV/BAV 状态为 `used_non_scoring`。
- 尚未完成 JHora/PyJHora 的逐星座 SAV/BAV raw parity。
- 本结果使用已见正事件，只是校正观察，不构成 V2.1 晋级验证。

机器报告：`docs/benchmark/public_real_case_23_case_v21_corrected_observation_2026_07_11.json`。
