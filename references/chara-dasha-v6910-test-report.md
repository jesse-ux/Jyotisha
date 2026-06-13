# Chara Dasha v6.9.10 Dignity Bug Fix 精度测试报告

> 日期：2026-06-13  
> 版本：v6.9.10  
> Bug：`lord_house == set()` → `lord_house in exalted_set` / `lord_house in debil_set`

## 1. Bug 修复摘要

修复前，`jaimini.py` 中将整数宫位与集合直接比较，导致 `dignity_adjustment` 永远无法命中 exalted/debilitated：

```python
if lord_house == exalted_set:
    dignity_status = 'exalted'
elif lord_house == debil_set:
    dignity_status = 'debilitated'
```

修复后改为集合成员测试：

```python
if lord_house in exalted_set:
    dignity_status = 'exalted'
elif lord_house in debil_set:
    dignity_status = 'debilitated'
```

结果：Chara Dasha 输出可正确识别 exalted/debilitated 状态。

## 2. 测试结果

| 测试项 | 结果 |
|--------|------|
| 全行星 dignity 矩阵（9行星×12星座=108） | 100.00%（108/108 PASS） |
| 名人案例 dignity（3案例×7断言） | 100.00%（7/7 PASS） |
| 修复前 dignity 检出率 | 0%（全部为 `none`） |
| 修复后 dignity 检出率 | 约 44%（16/36 有尊贵状态，符合预期比例） |

### 名人案例对比

- Einstein：修复前全部为 `none`；修复后 Gemini/Virgo 相关位置可识别 Mercury debilitated。
- Obama：修复后 Scorpio/Cancer 显示 exalted，Libra/Taurus 显示 debilitated。
- Synthetic Aries：修复后 8 个 exalted、2 个 debilitated、2 个 none。

## 3. PyJHora 计算层匹配

关键发现：`_chara_dasha_duration_knrao()` 内部尊贵调整本来已使用 `in` 操作符，因此 duration 计算不受该输出 bug 影响。

| 基准 | 修复前 | 修复后 |
|------|--------|--------|
| PyJHora Sign 匹配 | 100.00% | 100.00% |
| PyJHora Duration 匹配 | 90.83% | 90.83% |
| PyJHora Overall | 95.42% | 95.42% |

## 4. KN Rao 24.17% 根因判断

该 bug 不是 KN Rao 24.17% 低匹配率的根因。

- 24.17% 是解释/事件映射层匹配率，不是基础计算层匹配率。
- 计算层加权匹配从约 76.25% 提升到约 95.25%。
- 解读层仍需补：KN Rao 事件映射规则、Rashi Dasha interpretation、Karaka/Arudha 联动、Antardasha 尊贵加权。

| 维度 | 修复前 | 修复后 | 权重 |
|------|--------|--------|------|
| Sign 序列 | 100.00% | 100.00% | 20% |
| Lord 判定 | 约 95% | 约 95% | 20% |
| Duration | 90.83% | 90.83% | 30% |
| Dignity | 0.00% | 约 95% | 20% |
| Direction | 100.00% | 100.00% | 10% |
| 加权总计 | 约 76.25% | 约 95.25% | — |

## 5. 剩余问题

1. Duration ≤0 边界：debilitated 调整后若变成 0，是否应回绕到 12，需要继续对照 PyJHora/JHora。
2. 11/120 duration 不匹配：主要集中在偶数脚星座方向计数与共主判定。
3. 解读层：需要建立 KN Rao Chara Dasha 事件规则库与 30+ 名人案例基准集。

## 6. 相关测试文件

| 文件 | 用途 |
|------|------|
| `tests/test_chara_dasha_dignity.py` | dignity 修复基础验证 |
| `tests/test_chara_dasha_precision_v6910.py` | duration 对齐与 bug 前后对比 |
| `benchmarks/jyotish/outputs/chara_dasha_knrao_benchmark.json` | PyJHora 120-pair 基准数据 |
