# High Granularity Technique Deepening Backlog

日期：2026-06-26  
范围：只针对当前 skill 已涉猎、但尚未封顶的细节级技法

## 总结

当前 skill 的问题并不是这些细节“完全没做”，而是：

1. 已有底层计算或初级解释
2. 但还未形成厚重、稳定、可反复调用的传统解释层
3. 有些已进入规则与测试层，却还没做成独立高成熟度专题

## 一、财富格局细节线

### 1. Lakshmi Yoga / 吉祥天女瑜伽

- 当前归属：`Yoga / 财富格局 / Dhana`
- 当前证据：
  - `scripts/yoga_expansion.py`
  - `scripts/yogas_doshas.py`
  - `references/consultation-case-library.md`
- 当前状态：**已涉猎**
- 还缺什么：
  - 与 Dhana Yoga、Raja Yoga、Venus/Jupiter 强度的联动解释模板
  - 与 D2/D9/D10、Shadbala、Ashtakavarga 的财富兑现链
  - 与大运/年运激活条件的标准化说明

### 2. 财富点 / Saham 类财富辅助点

- 当前归属：`Sahams / Tajika / 年运辅助点`
- 当前证据：
  - `tests/test_tajika.py`
  - `SKILL.md` 中 `vivah-saham`
  - registry 中 `Sahams / 特殊点`
- 当前状态：**已涉猎但未封顶**
- 还缺什么：
  - 财富类 Saham 的解释层
  - Saham 权重与传统软件黑盒一致性
  - 与年度事件裁决的主次排序

## 二、星宿人格与天赋线

### 3. Ashwini 等 Nakshatra 的天赋特征

- 当前归属：`Nakshatra Advanced / Muhurta / Tara Bala`
- 当前证据：
  - `scripts/nakshatra_advanced.py`
  - `scripts/muhurtha_election.py`
  - `scripts/kalachakra_dasha.py`
- 当前状态：**已涉猎**
- 还缺什么：
  - 每个 Nakshatra 的天赋、阴影、职业倾向、关系模式、灵性主题
  - Pada 细分的人格差异
  - 与 D1/D9/UL/Karaka 的交叉解释模板

## 三、上升点精细定位线

### 4. 上升点度数定位

- 当前归属：`Lagna / Ascendant / Rectification / Special Lagnas / Divisional Ascendants`
- 当前证据：
  - `scripts/divisional_charts_extended.py`
  - `scripts/bhava_bala.py`
  - `scripts/sudarshana_chakra.py`
  - `scripts/_compute_one_chart.py`
- 当前状态：**明确已涉猎**
- 还缺什么：
  - 上升点度数对体貌、气场、人生发动方式的解释模板
  - Asc degree 与 Nakshatra / Pada 的联合解释
  - 出生时间矫正中的度数敏感区标准化说明

## 四、紧密合相与超细相位线

### 5. 紧密合相位的星体影响

- 当前归属：`Aspects / Orb / Conjunction / Combustion / Graha Yuddha`
- 当前证据：
  - `tests/test_aspects.py`
  - `references/retrograde-combustion-war-guide.md`
  - `scripts/yoga_expansion.py`
  - `scripts/yoga_engine.py`
- 当前状态：**已涉猎且有测试**
- 还缺什么：
  - 0°30' / 1° / 3° / 5° 等不同紧密级别的解释厚度
  - 凶星 vs 吉星紧密合相的现代案例口径
  - 紧密合相 + combust + graha yuddha 的复合判定模板

## 五、高阶解释层整合线

### 6. Avastha / Vargottama / Pushkara / RTN

- 当前归属：`Strength / D9 / Deep Varga / High-order interpretation`
- 当前证据：
  - registry 中 `Avastha` / `Vargottama` / `Pushkara`
  - `references/deep-varga-avastha-execution-guide.md`
  - `references/high-order-d9-execution-guide.md`
- 当前状态：**已涉猎但未形成传统高手式整合裁决层**
- 还缺什么：
  - 标准化综合口径
  - 吉星/凶星 Vargottama 的正反分类模板
  - Pushkara 与 Neecha Bhanga / D9 兑现度的组合说明

## 优先级建议

### P1

1. Ashwini 等 Nakshatra 深层人格/天赋模板
2. Lakshmi / Dhana / 财富激活链
3. 紧密合相多层解释模板

### P2

4. 上升点度数人格化解释
5. 高阶 Avastha / Vargottama / Pushkara 组合模板
6. Saham 类财富辅助点解释层

## 一句话判断

**这些技法大多已经在 skill 中“有根”，但还没有全部长成传统高手级的厚解释树冠。**
