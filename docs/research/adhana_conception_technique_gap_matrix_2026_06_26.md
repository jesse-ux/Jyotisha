# Adhana / Nisheka / 受孕盘 技法缺口矩阵

日期：2026-06-26
范围：基于 `/Users/wuyongnaren/文件仓库/印度占星文章/受孕/IMG_3216.JPG` 至 `IMG_3222.JPG` 六张截图，核对当前主仓 skill 是否已具备对应技法。

## 结论摘要

当前 skill **不具备完整的 Adhana / Nisheka / 受孕盘 专项体系**。

已有能力主要是基础零件：

- D12 / Dwadasamsa
- Gulika / Maandi
- Tithi / Vara / Panchanga
- Ghati / Hora / Ghatika 时间单位
- Special Lagnas（HL / GL / VL / PP / ViL）

缺失的是把这些零件串成“从出生盘反推受孕盘”的专用 workflow、公式固化、案例验证与解释模板。

## 截图涉及的技法拆解

| 截图主题 | 技法/规则 | 当前状态 | 证据/落点 | 备注 |
|---|---|---|---|---|
| 受孕盘（2）总体概述 | Adhana / Nisheka / 受孕盘 专项体系 | 缺失 | 全仓未发现 `Adhana`/`Nisheka` 专门模块 | 只有零件，没有整套引擎 |
| 受孕盘（2）总体概述 | 273 天妊娠周期规则 | 缺失 | 未发现专门实现 | 截图里作为核心 shortcut 出现 |
| 受孕盘（2）总体概述 | 男女差异规则 | 缺失 | 未发现专门实现 | 需权威来源核实后接入 |
| 受孕盘（3） | Adhana Lagna（受孕盘上升） | 缺失 | 无 `Adhana Lagna` 命令/输出路径 | 当前只有 HL/GL/VL/PP/ViL |
| 受孕盘（4） | Adhana Candra（受孕盘月亮） | 缺失 | 无 `Adhana Candra` 命令/输出路径 | 当前只有出生盘 Moon 与 Panchanga |
| 受孕盘（4） | 通过 D12 反推受孕盘月亮 | 部分具备 | `scripts/varga.py`, `scripts/divisional_yoga.py` | 有 D12 计算，但没有“反推月亮” workflow |
| 受孕盘（5） | 通过受孕盘上升反推出生盘上升 | 缺失 | 无专门实现 | 截图强调 Badarayana / Narada 传承方法 |
| 受孕盘（5） | Ghati 数换算与上升点回推 | 部分具备 | `scripts/special_lagnas.py`, `scripts/jaimini.py` | 有 Ghati/Ghatika 基础，但不是受孕盘算法 |
| 受孕盘（5） | 7 宫 / Kendra 约束法 | 缺失 | 无专门实现 | 需要封装为规则链 |
| 受孕盘（6） | 步骤总览 / Shortcut 流程 | 缺失 | 无专门 workflow | 可以作为第一版实现目标 |
| 受孕盘（6） | LMP / EDD / 产期倒推 | 缺失 | 无专门实现 | 偏实务流程，适合单独模块 |
| 受孕盘（6） | 出生星期 / 日主日 / 日月差 Ghati 推断 | 部分具备 | `scripts/muhurta.py`, `scripts/tithi_lord.py` | 有 Vara/Tithi，但未串成受孕盘步骤 |
| 受孕盘（7） | 案例法 / 样本推演 | 缺失 | 无 benchmark / oracle case | 需后续建立真实或公开案例集 |
| 全部截图 | Gulika 参与受孕盘计算 | 已具备基础 | `scripts/prashna.py`, `_compute_one_chart.py` | 可作为受孕盘引擎输入件 |
| 全部截图 | D12 / Dwadasamsa | 已具备基础 | `scripts/varga.py`, `scripts/divisional_charts_extended.py` | 当前仅能计算，不会专项解释 |
| 全部截图 | Ghati / Ghatika 时间框架 | 已具备基础 | `scripts/special_lagnas.py`, `scripts/jaimini.py` | 后续应复用，不必重写 |

## 当前可复用资产

### 1. D12 计算

- `scripts/varga.py`
- `scripts/divisional_yoga.py`
- `scripts/divisional_charts_extended.py`

用途：
- 作为 Adhana Candra / 受孕盘月亮反推的基础件

### 2. Gulika / Maandi

- `scripts/prashna.py`
- `scripts/_compute_one_chart.py`

用途：
- 作为截图案例里受孕盘步骤的敏感点输入

### 3. Ghati / Ghatika / Special Lagnas

- `scripts/special_lagnas.py`
- `scripts/jaimini.py`

用途：
- 复用 Ghati / Hora / Ghatika 计时骨架
- 不必重新写底层换算

### 4. Tithi / Vara / Panchanga

- `scripts/muhurta.py`
- `scripts/tithi_lord.py`

用途：
- 承接截图中“出生星期”“月亮度数”“Tithi 相关约束”的步骤化规则

## 真正缺的不是零件，而是四件事

1. `adhana.py` 或同等模块
- 输入：出生时间、出生盘 Moon / Gulika / Asc / D12
- 输出：Adhana Lagna、Adhana Candra、候选受孕窗口、规则解释链

2. 规则来源固化
- 需要把截图中的 Badarayana / Narada / Saravali 等规则拆成结构化规则
- 目前还只是文章级线索

3. benchmark / case
- 需要公开案例或至少内部样本，验证受孕盘反推是否稳定

4. interpretation template
- 即使算出来，也还缺“怎么讲”的解释模板

## 最高优先级落地方向

### P0

实现 `受孕盘步骤总览版`，先不追求全部细枝末节：

- 输入出生盘
- 输出：
  - D12
  - Gulika
  - Ghati-based sensitive timing
  - 候选 Adhana Lagna
  - 候选 Adhana Candra
  - 规则链说明

### P1

补全截图中的：

- 273 天规则
- 7 宫 / Kendra 限制
- LMP / EDD 反推辅助

### P2

做案例与解释模板：

- 公开案例 benchmark
- “受孕盘”专题解释模板

## 直接回答“这些截图里的技法，我们有吗？”

严谨回答：

- **完整体系：没有**
- **底层零件：大部分有**
- **可立即复用的核心基础：D12 / Gulika / Ghati / Hora / Vara / Tithi**
- **真正缺口：Adhana/Nisheka 专项 workflow 与验证闭环**

## 下一步建议

下一轮直接做：

1. 建 `tests/test_adhana.py`
2. 写第一版 `scripts/adhana.py`
3. 先落地：
   - D12-based candidate logic
   - Ghati timing scaffold
   - Gulika input
   - explanatory trace

不要先追求“所有古典分歧一次做完”；先把最短闭环版本做出来，再逐条加传统变体。
