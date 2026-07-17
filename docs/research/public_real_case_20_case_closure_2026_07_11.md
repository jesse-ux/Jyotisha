# 20 个公开真实案例回放与技法闭环（2026-07-11）

## 结论

本轮新增 10 个独立 holdout 案例，与首批 10 案例合并为 20 个公开事件。V2 规则在查看 holdout 结果前冻结，只增加三层通用技术：Rahu/Ketu 定位星、D9/D10 上升主与主题宫主、Amatyakaraka/Darakaraka。

holdout 上，V1 正事件激活召回从 `0.70` 升至 `0.80`，精确标签率保持 `0.30`，blocked 保持 `0`。按预注册门槛，V2 可以进入主链。这个 `0.80` 不是科学预测准确率：样本全是已发生的正事件，没有负样本，无法计算 specificity、false-positive rate 或 balanced accuracy。

机器报告：

- `docs/benchmark/public_real_case_holdout_v1_2026_07_11.json`
- `docs/benchmark/public_real_case_holdout_v2_2026_07_11.json`
- `docs/benchmark/public_real_case_holdout_comparison_2026_07_11.json`
- `docs/benchmark/public_real_case_20_case_closure_2026_07_11.json`

## 样本设计

- 出生时间：Astro-Databank Rodden `A/AA`。
- 事件：事业公开成就或法律婚姻的明确日期。
- 事件来源：官方机构优先；官方资料缺失时使用已核验二手资料。
- 域平衡：事业 10，婚姻 10。
- holdout 平衡：事业 5，婚姻 5；A 5，AA 5。
- 隐私：只使用公众人物公开资料，不含用户出生信息或个人反馈。

## 20 案例结果

| # | 人物 | 事件域 | 日期 | V2 分数 | 结果 |
|---|---|---|---|---:|---|
| 1 | Steve Jobs | career | 2007-01-09 | 7 | strong_hit |
| 2 | Barack Obama | career | 2008-11-04 | 1 | miss |
| 3 | Arnold Schwarzenegger | career | 2003-10-07 | 2 | miss |
| 4 | Meryl Streep | career | 1983-04-11 | 6 | weak_hit |
| 5 | Jennifer Aniston | career | 2002-09-22 | 7 | strong_hit |
| 6 | William, Prince of Wales | marriage | 2011-04-29 | 6 | weak_hit |
| 7 | Angelina Jolie | marriage | 2014-08-23 | 6 | weak_hit |
| 8 | Frida Kahlo | marriage | 1929-08-21 | 7 | strong_hit |
| 9 | Snoop Dogg | marriage | 1997-06-14 | 10 | strong_hit |
| 10 | Walt Disney | marriage | 1925-07-13 | 10 | strong_hit |
| 11 | Albert II, Prince of Monaco | career | 2005-04-06 | 9 | strong_hit |
| 12 | Boy George | career | 1984-02-28 | 6 | weak_hit |
| 13 | Ingrid Bergman | career | 1945-03-15 | 8 | strong_hit |
| 14 | Alanis Morissette | career | 1996-02-28 | 4 | weak_hit |
| 15 | Celine Dion | career | 1988-04-30 | 5 | weak_hit |
| 16 | Paul McCartney | marriage | 1969-03-12 | 7 | strong_hit |
| 17 | Johnny Depp | marriage | 2015-02-03 | 6 | weak_hit |
| 18 | Nicole Kidman | marriage | 2006-06-25 | 3 | miss |
| 19 | Demi Moore | marriage | 1987-11-21 | 0 | miss |
| 20 | Chelsea Clinton | marriage | 2010-07-31 | 5 | weak_hit |

合并结果：`8 strong + 8 weak + 4 miss + 0 blocked`。事业与婚姻两域各自都是 `0.80` 正事件激活召回、`0.40` 精确标签率。

## V2 带来的可复现变化

- 首批训练集：正事件召回仍为 `0.80`，精确标签率由 `0.30` 升至 `0.50`。Jobs 和 Aniston 从 weak 升为 strong。
- 未见 holdout：Celine Dion 从 `3/miss` 升为 `5/weak_hit`，依据为 Mercury 同时成为 D10 上升主与 Amatyakaraka。
- Boy George、Ingrid Bergman、Johnny Depp、Chelsea Clinton 得分增加，但未跨越结果等级或只增强已有等级。
- V2 没有增加 blocked，也没有改变阈值。

## 四个剩余漏判揭示的技法债

### 1. Obama 与 Schwarzenegger：普通事业层不足以覆盖政治身份跃迁

当前回放把所有事业事件统一映射到 `10/6/9/11 + D10/A10`。总统当选、州长当选属于公众权力与国家身份跃迁，还需要独立审计：D10 Raja Yoga、D10 宫主相位、A10/AL 联动、Sun/AmK/政治权力指标、年度 Varshaphala。不能为两个 miss 临时提高通用事业分数。

### 2. Kidman 与 Demi Moore：Narayana 只审计 MD，遗漏 AD/PD 语义

两案事件时的 Narayana 包中都出现 Venus 主导的下级周期，但 V2 只对 Narayana MD 的主题星座和宫主加分。完整 MD/AD/PD 主题收敛是明确的 V3 候选；它必须在第三批新 holdout 上验证后才能进入生产评分，不能用当前两案反向调参。

### 3. PD/PrAD 已能展开，但尚非外部验证闭环

`scripts/vimshottari_subperiod_timeline.py` 可从本仓 AD 边界按标准比例展开 PD/PrAD。它适合提供月/周级候选窗，不应在没有 JHora/PyJHora/VedAstro 同盘原始输出时当作已验证 oracle。

### 4. 年度层与 KP 仍是 partial

- `Varshaphala/Muntha` 可运行，但年主裁决仍有简化实现，外部 Tajika oracle 未闭环。
- 本地 KP 可算 sub-lord/significator，但宫位层仍含“星座中点代替精确 cusp”的近似，不能称为完整 KP 事件裁决。
- 本轮修复了 `scripts/muntha.py` 独立导入时遗漏 `List` 导致的崩溃，并新增回归测试；这只是恢复可运行性，不等于年度预测精度已验证。

## Technique Audit Table

| Technique | 状态 | 说明 |
|---|---|---|
| D1 + Functional Benefic/Malefic | used | 20/20 |
| D9 + UL + Darakaraka | used | 10 个婚姻事件 |
| D10 + A10 + Amatyakaraka | used | 10 个事业事件 |
| Vimshottari MD/AD | used | 20/20 |
| Narayana Dasha | used | 20/20；AD/PD 完整语义仍待 V3 |
| Double Transit PAC | used | 20/20 |
| Rahu/Ketu dispositor | used | V2 正式评分层 |
| Vimshottari PD/PrAD | partial | 比例展开可用，外部同盘未验证 |
| Tajika/Varshaphala/Muntha | partial | 本地简化层；外部 oracle 未闭环 |
| KP exact cusp/significators | partial | sub-lord 可用；精确 cusp 闭环不足 |
| VedAstro official raw | blocked | `official_snapshot_budget_exhausted` |
| PyJHora/JHora/jyotishganit parity | blocked | canonical raw comparison 未完成 |
| MEVG / Global Web Evidence | used | 20 组公开出生/事件来源 |
| Real Case Calibration | used | 10 discovery + 10 frozen holdout |
| Negative controls | blocked | 无已核验“不发生事件”日期 |

## 新增 holdout 主要来源

- 出生时间：Astro-Databank VIP 页面，逐案 URL 已保存在 `references/real_case_calibration/replay_manifest_holdout_v2.json`。
- 事业事件：[Monaco Palace](https://www.palais.mc/en/princely-family/h-s-h-prince-albert-ii/biography-1-9.html)、[Oscars 1945](https://www.oscars.org/oscars/ceremonies/1945)、[Eurovision 1988](https://eurovision.tv/event/dublin-1988)。
- 婚姻事件：[Variety - Johnny Depp](https://variety.com/2016/biz/news/johnny-depp-amber-heard-divorce-settlement-1201837685/)、其余核验二手来源逐案保存在 holdout manifest。

## 已落地优化

1. V2 通过 holdout 门槛，统一 orchestrator 改读 20 案例合并报告。
2. 新增 V1/V2 纯比较模式，禁止比较命令重复跑两遍底层引擎导致超时。
3. 合并报告自动输出 domain summary、holdout promotion、Technique Audit 与 technique debt。
4. 修复 Muntha 独立模块导入错误并加测试。
5. 保留四个 miss，不用事后调参掩盖。

下一次真正提高可信度的最小方案：第三批 10 案例冻结 holdout，其中加入政治/公众身份事件与经核验负样本；只验证 Narayana AD/PD、D10 Raja Yoga/相位和年度层，不再扩展更多名称。
