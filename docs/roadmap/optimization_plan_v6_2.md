# 印度占星 Skill v6.2 优化路线图

> **版本基准**: v6.1.12 (2026-06-11)
> **文档版本**: v1.0
> **原则**: 严谨、详细、不设定完成时间、优先复用开源、逐条可验证

---

## 一、当前状态总览（实事求是）

### 1.1 技法注册表状态

| 状态 | 数量 | 占比 |
|------|------|------|
| covered | 31 | 64.6% |
| partial | 17 | 35.4% |
| missing | 0（registry中） | 0% |

**但**: `feature-gap-matrix-2026.md` 与 `technique_registry.json` 存在口径差异。Registry 中标记为 covered 的部分技法（如 Shadbala、Bhava Chalit）在 gap matrix 中仍有简化项；gap matrix 中标记为 ❌ 的部分功能（如 Darakaraka、RTN）实际已在 v6.1.10 接入 full-reading。**本文档以代码实际实现为真，以 registry 为辅助参考。**

### 1.2 关键精度指标

| 模块 | 当前指标 | 目标 | 缺口 |
|------|---------|------|------|
| Yoga识别 | F1=95.22%, P=96.48%, R=93.99% | F1≥96% | FN=63条, FP=36条 |
| Chara Dasha | Sign=100%, Dur=91.67%, Overall=95.83% | Overall≥98% | Aquarius/Scorpio共主判定 |
| Shadbala | 内部不变量1200/1200通过 | 外部绝对值校准 | 无JHora对标数据 |
| Ashtakavarga | SAV=337/386校准通过 | 完整PAV+Sodhita | 缺PAV展开、Sodhita减法 |
| Vimshottari | 未正式benchmark | 与PyJHora对标 | 待建立oracle测试 |
| Transit | 340/340字段 Swiss Ephemeris匹配 | 保持100% | 无已知缺口 |

### 1.3 已知计算缺口（经代码验证）

| # | 缺口项 | 影响 | 验证状态 |
|---|--------|------|---------|
| 1 | **Prastara Ashtakavarga (PAV)** | 行运精细评分缺失 | 完全无代码 |
| 2 | **Sodhita Ashtakavarga** | AV吉凶修正层缺失 | 完全无代码 |
| 3 | **Kakshya评分** | 行星度数区间力量量化缺失 | 完全无代码 |
| 4 | **Kantaka Shani** | Sade Sati细分阶段缺失 | 仅有文档，无引擎代码 |
| 5 | **Bhava Bala** | 宫位力量计算缺失 | 完全无代码 |
| 6 | **D81/D108/D144/自定义分盘** | 精微分盘缺失 | 完全无代码 |
| 7 | **Vimshottari外部benchmark** | 大运精度未验证 | 无oracle测试 |

### 1.4 文档与代码不一致项

| 文档 | 声明 | 实际代码状态 | 修复动作 |
|------|------|-------------|---------|
| `technique-capability-matrix.md` | 不存在 | registry替代 | 删除或重定向 |
| `quick-reference-guide.md` | 引用 `birth-time-rectification-guide.md` | 文件不存在 | 修正为 `-advanced.md` |
| `quick-reference-guide.md` | 引用 `cmd_rectify` 子命令 | jyotish_engine.py中不存在 | 删除错误引用 |
| `quick-reference-guide.md` | 引用 `birth_time_rectification.py` | scripts/下不存在 | 清理引用 |
| `COVERAGE_AUDIT_REPORT.md` | v3.13.1 | 实际v6.1.12 | 文档版本需更新 |
| `SKILL.md` | 版本号v6.1.8 | 实际v6.1.12 | 更新版本号 |

---

## 二、优化原则

1. **真代码优先**: 不以文档声明为准，以 `scripts/*.py` 实际可执行代码为准。
2. **Benchmark驱动**: 任何精度优化必须有 PyJHora / Swiss Ephemeris / 公开书例作为 oracle，不接受"感觉对了"。
3. **开源复用优先**: 已有 MIT/AGPL 开源实现的，优先翻译/适配，不从零造轮子。
4. **增量验证**: 每项改动必须通过 `python3 -m py_compile` + 相关 benchmark + `pytest` 三重门禁。
5. **文档同步**: 代码变更后，同步更新 `technique_registry.json`、`SKILL.md`、`CHANGELOG.md`。
6. **诚实标注**: partial 就是 partial，不因情感因素升级为 covered；升级必须有 benchmark 证据。

---

## 三、P0 精度修复层（影响解读正确性）

> **定义**: 当前已标记为 covered 但存在已知精度缺口、可能导致解读错误的计算模块。

### P0.1 Chara Dasha 剩余 4.2% 不匹配修复

**目标**: 将 Overall 从 95.83% 提升至 ≥98%。

**技术方案**:
- 文件: `scripts/jaimini.py`
- 函数: `_resolve_chara_dasha_lord()`（已预留扩展点）
- 问题: Aquarius/Scorpio 的 Rahu/Ketu 共主动态判定当前使用传统宫主（Saturn/Mars），而 PyJHora 使用 `_stronger_planet_new()` 完整尊严比较链。
- 实现: 复制 PyJHora `_stronger_planet_new` 逻辑（尊严层级: exalted > own > friendly > neutral > enemy > debilitated；同层级比较 Shadbala 力量），在 `_resolve_chara_dasha_lord()` 中当 sign 为 Aquarius 或 Scorpio 时，动态比较 Saturn vs Rahu 或 Mars vs Ketu 的尊严，返回较强者。

**验证方法**:
- 扩展 `benchmarks/jyotish/scripts/run_chara_dasha_knrao.py`
- 10案例×12星座 = 120对基准已建立，修复后重新跑全量
- 目标: Overall ≥98%（允许 Mean/True Node 口径差异导致的固有偏差）

**开源复用**:
- PyJHora `jhora/panchanga/dhasa/jaimini_dhasa.py:_stronger_planet_new()`（AGPL，算法翻译为独立实现）

**预期效果**:
- 约 5/120 案例的 duration 差异消除
- Sign 匹配保持 100%

---

### P0.2 Yoga 引擎 FN/FP 收敛

**目标**: F1 从 95.22% 提升至 ≥96%，FN 从 63 降至 ≤50，FP 从 36 降至 ≤30。

**技术方案**:
- 文件: `scripts/yoga_engine.py`
- 当前: 60张测试图，82条可对比规则，FN=63, FP=36
- 策略: **准确率优先**，只接受来源语义明确且预验证不增加 FP 的规则优化。

**具体待分析项**（基于 v6.1.8 验证报告 `references/validation_logic_report.json`）:
1. **Thrikaala Gnana Yoga**: 当前保守口径（D9/D60 上下文已注入），需评估是否可适度放宽前提条件而不增加 FP。
2. **Dharidhra Yoga**: 方法已恢复，评估是否有剩余 FN 可归因于 Navamsa 弱势定义差异。
3. **Parannabhojana Yoga**: 与 Dharidhra 类似，检查分盘口径。
4. **Nishkapata Yoga**: BVR-205 友好星座条件已恢复，评估剩余 FN。
5. **Kapata Yoga**: v6.1.8 已评估"4宫主受凶星相位"候选会增加 FP 且无 FN 收益，保持原逻辑；若后续发现新的 FN 收益证据，重新评估。

**验证方法**:
- 运行 `scripts/validate_logic_v2.py`
- 对比 PyJHora 同案例输出（需建立 10-20 个公开名人案例的 Yoga 清单 oracle）
- 每项规则变更前后对比 FP/FN 变化

**开源复用**:
- PyJHora `jhora/panchanga/yoga.py`（参考其 Yoga 判定逻辑，AGPL 翻译）

**预期效果**:
- F1 ≥96%，FP ≤30，FN ≤50

---

### P0.3 Vimshottari Dasha 外部 Benchmark 建立

**目标**: 建立 Vimshottari 的 PyJHora oracle 基准，验证 MD/AD/PD 三层时间边界。

**技术方案**:
- 新文件: `benchmarks/jyotish/scripts/run_vimshottari_compare.py`
- 参照 `run_chara_dasha_knrao.py` 结构
- 输入: 10个公开/虚构 smoke case（与 Chara Dasha benchmark 共用样本池）
- Oracle: PyJHora `Vimsottari.get_dhasa_bhukthi(dob, tob, place, divisional_chart_factor=1)`
- 对比字段: MD主星、MD起始日期、MD结束日期、AD主星、AD起始日期、PD主星、PD起始日期

**验证方法**:
- 建立 120 对基准（10案例 × 12 字段）
- 目标: ≥95% 字段级匹配（允许时区/闰秒差异）
- 若发现系统偏差，定位至 `scripts/dasha_calculator.py` 或 `scripts/dasha_calculator_enhanced.py`

**开源复用**:
- PyJHora `jhora/panchanga/dhasa/vimsottari.py`（AGPL，算法参考）

**预期效果**:
- 明确 Vimshottari 精度等级
- 为 `technique_registry.json` 中 `vimshottari_dasha` 补充 benchmark 证据

---

### P0.4 Ashtakavarga 完整 PAV 展开表

**目标**: 实现 Prastara Ashtakavarga（行星×宫位展开表），补齐 AV 行运评分的计算基础。

**技术方案**:
- 文件: `scripts/ashtakavarga.py`（当前 v2.1）
- 新增函数: `calc_prastara_av(birth_info)`
- 算法: 基于已有 BAV（Bhinna Ashtakavarga），对每个行星在每个宫位的贡献展开为 8 个行星（含 Asc）的单独贡献标记。PyJHora `ashtakavarga.py:get_prastara_ashtakavarga()` 可直接参考。
- 输出: 7×12×8 三维矩阵（7行星 × 12宫位 × 8贡献源）

**验证方法**:
- 与 PyJHora `prastara_ashtakavarga()` 对比 10 个案例
- 不变量检查: PAV 所有行求和 = BAV 对应行星值；PAV 所有列求和 = BAV 对应宫位值

**开源复用**:
- PyJHora `jhora/panchanga/ashtakavarga.py:get_prastara_ashtakavarga()`（AGPL 翻译）

**预期效果**:
- AV 行运评分从 "近似" 升级为 "精确"
- 为 `ashtakavarga` 子命令新增 `--prastara` 选项

---

### P0.5 Sodhita Ashtakavarga 实现

**目标**: 实现 Sodhita（减法）Ashtakavarga，用于修正 AV 吉凶判断。

**技术方案**:
- 文件: `scripts/ashtakavarga.py`
- 新增函数: `calc_sodhita_av(birth_info, prastara_av)`
- 算法: BPHS 标准 Sodhita 流程——从每个宫位的 BAV 中减去该宫位的 Saturn 贡献、Mars 贡献和 Sun 贡献（若结果为负则取0）。PyJHora `get_sodhita_ashtakavarga()` 可直接参考。
- 输出: 7×12 矩阵（Sodhita 后的每个行星-宫位值）

**验证方法**:
- 与 PyJHora `sodhita_ashtakavarga()` 对比
- 不变量: Sodhita AV ≤ 原始 BAV；Sodhita SAV ≤ 原始 SAV

**开源复用**:
- PyJHora `jhora/panchanga/ashtakavarga.py:get_sodhita_ashtakavarga()`（AGPL 翻译）

**预期效果**:
- 行运吉凶判断增加 Sodhita 修正层
- 为 `ashtakavarga` 子命令新增 `--sodhita` 选项

---

### P0.6 Kakshya 评分系统

**目标**: 实现 Kakshya（度数区间力量）评分，为 Transit 精确触发提供度数级量化。

**技术方案**:
- 新文件: `scripts/kakshya.py`
- 算法: 每个宫位分为 8 个 Kakshya（区间），每个区间由特定行星守护。行星落入某区间时，获得该区间守护行星的加持或削弱。PyJHora `kakshya.py` 有完整实现。
- 关键: Kakshya 区间划分基于行星平均运动速度（太阳30°、月亮15°等），非等分。

**验证方法**:
- 与 PyJHora `kakshya.get_kakshya_spurhta()` 对比 10 个案例
- 检查每个行星的 Kakshya 归属和力量值

**开源复用**:
- PyJHora `jhora/panchanga/kakshya.py`（AGPL 翻译）

**预期效果**:
- Transit 触发精度从 "星座级" 提升至 "度数区间级"
- 接入 `full-reading.modules.transit_kakshya`

---

## 四、P1 核心升级层（partial → covered）

> **定义**: 当前标记为 partial、代码已存在但有限制，经优化后可升级为 covered 的技法。

### P1.1 Shadbala 外部绝对值校准

**目标**: 将 Shadbala 从 "内部一致" 升级为 "外部绝对值可信"。

**技术方案**:
- 文件: `scripts/shadbala.py`
- 当前简化项:
  1. Nathonnata Bala: 二值化（白天/夜晚），应改为基于赤纬的比例计算
  2. Saptavargaja Bala: 部分子分盘近似，应改为调用 `varga.py` 实际分盘
  3. Chesta Bala: 速度分档近似，应改为基于真实速度比例的连续计算
  4. Drik Bala: 简化相位权重，应改为基于确切度数的相位力量公式
- 对标: PyJHora `shad_bala.py` 完整实现（AGPL，算法参考）

**具体修复步骤**:
1. **Nathonnata Bala**: 使用 Swiss Ephemeris 获取太阳赤纬，计算 `nathonnata_bala = sin(declination) * 标准化因子`，替代当前二值化。
2. **Saptavargaja Bala**: 调用 `divisional_charts_extended.py` 实际计算 D1/D2/D3/D7/D9/D10/D12，对每个分盘计算 dignity 得分后聚合，替代当前近似表。
3. **Chesta Bala**: 使用 Swiss Ephemeris 获取行星真实日运动速度（`swe.calc_ut()` 的 `speed` 字段），对照平均速度计算比例，替代当前分档。
4. **Drik Bala**: 实现完整相位力量公式——`aspect_strength = (180 - |actual_orb|) / 180 * base_strength`，对所有7行星的特殊相位和Rasi Drishti分别计算后聚合。

**验证方法**:
- 扩展 `benchmarks/jyotish/scripts/run_shadbala_invariants.py` 为 `run_shadbala_pyjhora_compare.py`
- 10案例 × 6种力量 × 7行星 = 420 个数值对比
- 目标: 与 PyJHora Shadbala 总分差异 ≤5%（因 Naisargika Bala 已对齐，主要差异应在 Chesta/Drik）
- 内部不变量保持 1200/1200 通过

**开源复用**:
- PyJHora `jhora/panchanga/shad_bala.py`（AGPL 算法翻译）
- jyotishganit `components/strengths.py`（MIT，已有 clone 在 references 中）

**预期效果**:
- `technique_registry.json` 中 `shadbala` 状态从 `partial` → `covered`
- full-reading 中 Shadbala 评估置信度上限解除

---

### P1.2 Bhava Chalit 完整实现

**目标**: 实现完整的 Bhava Chalit（变动宫位）行星重新分配。

**技术方案**:
- 文件: `scripts/bhava_chalit.py`（当前只有宫位计算，无行星重分配）
- 新增函数: `assign_planets_to_chalit(birth_info, house_cusps)`
- 算法: 对每个行星，比较其经度与相邻两个宫位的宫头经度。若行星距某宫头 < 阈值的 1/3，归入该宫位；否则按常规星座归属。PyJHora `bhava_chalit_chart()` 可直接参考。
- 输出: Chalit 行星分配表 + Chalit D1 图数据

**验证方法**:
- 与 PyJHora `bhava_chalit_chart()` 对比 10 个案例
- 检查每个行星的 Chalit 宫位分配

**开源复用**:
- PyJHora `jhora/panchanga/chart.py:bhava_chalit_chart()`（AGPL 翻译）

**预期效果**:
- `technique_registry.json` 中 `bhava_chalit` 状态从 `partial` → `covered`
- full-reading 中宫位分析增加 Chalit 视角

---

### P1.3 Sudarshana Chakra 传统实现

**目标**: 实现传统 Sudarshana Chakra（三参考点盘：Lagna + Chandra + Surya）。

**技术方案**:
- 新文件: `scripts/sudarshana_chakra.py`
- 当前替代方案: D1-D9-D10 三角验证（非传统 Sudarshana）
- 算法: 以 Lagna 为第1宫绘制的 D1 图 + 以 Moon 为第1宫重新排列的图 + 以 Sun 为第1宫重新排列的图。三个图中同一宫位/行星配置的一致性用于确认事件。
- 输出: 三个参考点盘 + 一致性标记

**验证方法**:
- 建立 5 个公开名人案例的三参考点盘
- 与 PyJHora `sudarshana_chakra()` 对比行星位置

**开源复用**:
- PyJHora `jhora/panchanga/chart.py:sudarshana_chakra()`（AGPL 翻译）

**预期效果**:
- `technique_registry.json` 中 `sudarshana_chakra` 状态从 `partial` → `covered`
- full-reading 中 "传统 Sudarshana" 从缺口声明变为实际输出

---

### P1.4 Tajika Yogas 完整覆盖

**目标**: 从简化规则扩展为完整的 Tajika Yoga 检测（Itasala、Ishkavala、Etc. + Vedha 阻碍逻辑）。

**技术方案**:
- 文件: `scripts/tajika.py`
- 当前: 简化规则（约 5-6 种基础 Yoga）
- 目标: 覆盖 PyJHora 的 10 种年度 Yoga 分类 + Vedha 阻碍逻辑
- 新增函数: `_detect_tajika_yogas_complete(varshaphala_data)`
- 算法翻译: PyJHora `tajika/yogas.py`（AGPL）

**具体 Yoga 列表**:
1. Itasala（友好相位）
2. Ishkavala（单向相位）
3. Vasala（无效相位）
4. Tambira（阻碍）
5. Kambira（双重阻碍）
6. Dakshina（右向）
7. Vama（左向）
8. Ubhaya（双向）
9. Vedha（穿刺阻碍）
10. Kuta（组合）

**验证方法**:
- 与 PyJHora `tajika_yogas()` 对比 10 个年运盘
- 检查每种 Yoga 的触发条件和阻碍逻辑

**开源复用**:
- PyJHora `jhora/panchanga/tajika/yogas.py`（AGPL 翻译）

**预期效果**:
- `technique_registry.json` 中 `tajika_yogas` 状态从 `partial` → `covered`
- 年运盘格局判断从高置信度上限升级为标准应期模块

---

### P1.5 Sahams 扩展至 36 种

**目标**: 从当前的 Vivah Saham 扩展为完整的 36 种 Saham 计算。

**技术方案**:
- 文件: `scripts/tajika.py`（当前只有 `calc_vivah_saham`）
- 新增函数: `calc_all_sahams(birth_info, year_lord_data)`
- 36 种 Saham 列表（标准 Tajika 体系）:
  - Vivah（婚姻）、Karma（事业）、Paradesa（ foreign）、Bandhu（兄弟姐妹）、Putra（子女）、
  - Vidya（教育）、Arogya（健康）、Marana（死亡）、Kala（时间）、Yasha（名声）等
- 每种 Saham 的公式基于特定行星经度的加减运算，参照 PyJHora `saham.py`。

**验证方法**:
- 与 PyJHora `saham.get_saham_longitude_list()` 对比 10 个案例
- 检查每种 Saham 的经度计算

**开源复用**:
- PyJHora `jhora/panchanga/tajika/saham.py`（AGPL 翻译）

**预期效果**:
- `technique_registry.json` 中 `sahams` 状态从 `partial` → `covered`
- 年运盘增加 36 个敏感点分析

---

### P1.6 Sade Sati 完整实现（含 Kantaka Shani）

**目标**: 从简化模型升级为完整的 Sade Sati + Kantaka Shani 细分阶段。

**技术方案**:
- 新文件: `scripts/sade_sati.py`（当前逻辑分散在 `jyotish_engine.py` 或文档中）
- 当前: 土星经过月亮前后星座的简化模型
- 完整实现:
  1. **Sade Sati 三阶段**: Rising（进入前星座）→ Peak（月亮星座）→ Setting（离开后星座）
  2. **Kantaka Shani**: 土星在第1/4/8/10宫时的额外压力标记
  3. **Ashtakavarga 修正**: Sade Sati 期间 Saturn 的 BAV 贡献修正压力程度
  4. **小周期**: 每个阶段内部按 Saturn 经过的 Nakshatra 细分

**验证方法**:
- 与 PyJHora `sade_sati.get_sade_sati_dates()` 对比 10 个案例
- 验证三阶段时间边界和 Kantaka Shani 标记

**开源复用**:
- PyJHora `jhora/panchanga/transit/sade_sati.py`（AGPL 翻译）

**预期效果**:
- `technique_registry.json` 中 `sade_sati` 状态从 `partial` → `covered`
- Transit 分析中 Saturn 压力评估从近似升级为精确

---

### P1.7 Pancha Mahapurusha Yoga 完整变体

**目标**: 覆盖燃烧、逆行、受克时的 Yoga 失效条件。

**技术方案**:
- 文件: `scripts/yoga_engine.py`
- 当前: 基础规则（Ruchaka/Bhadra/Hamsa/Malavya/Shasha 在 Kendra + own/exalted）
- 缺失: 失效条件——若 Yoga 主星燃烧（combust）、逆行（retrograde）、受凶星相位/合相，则 Yoga 效力减弱或失效。
- 新增函数: `_check_yoga_validity(planet, chart_data)`
- 检查项: Combustion（距 Sun < 8-15°）、Retrograde、Malefic aspects（Saturn/Mars/Rahu）、Debilitation in Navamsa

**验证方法**:
- 选择 5 个有 Pancha Mahapurusha 但主星受克的案例
- 验证 Yoga 被正确降级或取消

**开源复用**:
- PyJHora `jhora/panchanga/yoga.py` 失效条件逻辑（AGPL 参考）

**预期效果**:
- `technique_registry.json` 中 `pancha_mahapurusha` 状态从 `partial` → `covered`
- Yoga 强度评分更准确

---

## 五、P2 覆盖扩展层（新增缺失技法）

> **定义**: 当前完全无代码实现、但属于专业 Jyotish 软件标准功能的技法。

### P2.1 高级分盘: D81/D108/D144 + 自定义 D-N

**目标**: 实现 D81（Navamsamsa）、D108、D144 和自定义分盘计算。

**技术方案**:
- 文件: `scripts/divisional_charts_extended.py`（当前已扩展至 D2-D60）
- 新增函数: `calc_d81(birth_info)`, `calc_d108(birth_info)`, `calc_d144(birth_info)`, `calc_custom_division(birth_info, n)`
- 算法: D81 = D9 的 D9；D108 = D12 的 D9；D144 = D12 的 D12。PyJHora `divisional_chart()` 支持任意 D-N。

**验证方法**:
- 与 PyJHora `divisional_chart(birth_info, divisional_chart_factor=81/108/144)` 对比
- 检查行星经度映射

**开源复用**:
- PyJHora `jhora/panchanga/chart.py:divisional_chart()`（AGPL 参考）

**预期效果**:
- 分盘覆盖从 16 种扩展至 19+ 种
- 接入 `varga-full` 子命令

---

### P2.2 Bhava Bala（宫位力量）

**目标**: 实现完整的 Bhava Bala 计算。

**技术方案**:
- 新文件: `scripts/bhava_bala.py`
- 算法: Bhava Bala = 宫位主星的 Shadbala × 宫位中行星的影响 × 宫位本身的位置因素（Kendra/Trikona/Dusthana）。PyJHora `bhava_bala.py` 有完整实现。
- 依赖: 需要先完成 P1.1（Shadbala 外部校准）。

**验证方法**:
- 与 PyJHora `bhava_bala.get_bhava_balas()` 对比 10 个案例

**开源复用**:
- PyJHora `jhora/panchanga/bhava_bala.py`（AGPL 翻译）

**预期效果**:
- 宫位分析增加力量量化层
- 为 `shadbala` 子命令新增 `--bhava` 选项

---

### P2.3 额外 Dasha 系统（Dwisaptati / Shattrimsa / Dwadashottari 等）

**目标**: 实现 3-5 种常用条件性 Dasha 系统。

**技术方案**:
- 优先级排序（按实用性和开源可复用性）:
  1. **Dwisaptati Sama Dasha**（72年周期，适用于特定 Tithi 条件）
  2. **Shattrimsa Sama Dasha**（36年周期）
  3. **Dwadashottari Dasha**（112年周期，适用于特定 Nakshatra 条件）
  4. **Sthira Dasha**（固定宫位 Dasha）
- 新文件: `scripts/dwisaptati_dasha.py`, `scripts/shattrimsa_dasha.py`, `scripts/dwadashottari_dasha.py`, `scripts/sthira_dasha.py`
- 每种 Dasha 的实现模式参照现有 `ashtottari_dasha.py` / `kalachakra_dasha.py` 结构。

**验证方法**:
- 与 PyJHora 对应 Dasha 模块对比时间边界
- 条件性 Dasha 需验证触发条件判断

**开源复用**:
- PyJHora `jhora/panchanga/dhasa/*.py`（AGPL 翻译）

**预期效果**:
- Dasha 系统从 7 种扩展至 10+ 种
- 五系统 Convergence 升级为多系统 Convergence

---

### P2.4 分盘中 Yoga 识别

**目标**: 在 D9/D10/D60 等分盘中运行 Yoga 引擎。

**技术方案**:
- 文件: `scripts/yoga_engine.py`
- 当前: Yoga 引擎只接收 D1 数据
- 修改: `detect()` 函数增加 `divisional_chart_data` 参数，在分盘数据中运行相同的 Yoga 规则
- 新增函数: `detect_in_varga(birth_info, varga_name, varga_data)`
- 调用点: `jyotish_engine.py` 的 `varga-full` 子命令中，对每个分盘计算 Yoga

**验证方法**:
- 选择 5 个公开案例，在 D9 中检测 Yoga
- 与 PyJHora 分盘 Yoga 对比

**开源复用**:
- PyJHora `jhora/panchanga/yoga.py`（AGPL 参考其分盘 Yoga 调用方式）

**预期效果**:
- full-reading 中 `modules.varga_full.*.yogas` 输出分盘 Yoga
- 技法覆盖度地图中 "分盘中 Yoga 识别" 从 ❌ 变为 ✅

---

### P2.5 Transit 精确触发搜索

**目标**: 实现精确到度分的 Transit 触发搜索。

**技术方案**:
- 新文件: `scripts/transit_search.py`
- 功能: 给定时间窗口和目标配置（如 "Saturn 合相 Moon"），搜索精确发生日期。
- 算法: 在给定窗口内逐日计算 Transit 行星位置，使用二分法逼近精确合相/相位时刻。
- 输入: 本命盘 + 起始日期 + 结束日期 + 目标配置
- 输出: 精确触发日期列表 + 度数误差

**验证方法**:
- 搜索已知天文事件（如 Saturn 回归），与 NASA/JPL 数据对比
- 验证精确日期误差 < 1 天

**开源复用**:
- Swiss Ephemeris `swe.calc_ut()`（已有）
- PyJHora `transit.py`（AGPL 参考）

**预期效果**:
- Transit 预测从 "月份级" 提升至 "日期级"
- 为 `transit` 子命令新增 `--search` 选项

---

## 六、P3 质量提升层（文档、测试、CI）

### P3.1 文档与代码一致性审计

**目标**: 消除所有文档与实际代码的不一致。

**具体任务**:
1. 更新 `SKILL.md` 版本号 v6.1.8 → v6.1.12
2. 更新 `COVERAGE_AUDIT_REPORT.md` 版本号 v3.13.1 → v6.1.12
3. 修正 `quick-reference-guide.md` 错误引用（3处）
4. 清理 `docs/roadmap/jyotish_technique_coverage_map.md` 中已修复的 ❌ 标记（Darakaraka、RTN、Chara Dasha 等）
5. 统一 `technique_registry.json` 与 `feature-gap-matrix-2026.md` 的口径

**验证方法**:
- 运行 `scripts/audit_capabilities.py --mode validate`
- 人工检查 3 个关键文档的版本号和引用

---

### P3.2 Benchmark 体系扩展

**目标**: 为每个 covered/partial 技法建立可复跑的 benchmark。

**已有 Benchmark**（12轮）:
- Round 1: 本地基线
- Round 2: Swiss Ephemeris 扩展对比
- Round 3: PyJHora 对比
- Round 4: Node Mode 对比
- Round 5: Arudha/A10 对比
- Round 6: Ashtakavarga 对比
- Round 6b: Ashtakavarga 表仲裁
- Round 6c: Ashtakavarga 书例
- Round 7: Chara Dasha 对比
- Round 8: Transit 真实过境对比
- Round 9: Shadbala 不变量
- Round 10: 解释回归

**待建立 Benchmark**:
- Round 11: Vimshottari Dasha 精度（P0.3）
- Round 12: Shadbala 外部绝对值（P1.1）
- Round 13: Yoga FN/FP 收敛（P0.2）
- Round 14: PAV + Sodhita AV（P0.4-P0.5）
- Round 15: Bhava Chalit 精度（P1.2）
- Round 16: Tajika Yogas 完整覆盖（P1.4）

**验证方法**:
- 每个新 benchmark 脚本需通过 `pytest` 集成测试
- benchmark 输出保存至 `benchmarks/jyotish/outputs/` 和 `reports/`

---

### P3.3 CI/CD 质量门禁完善

**目标**: 建立自动化的 pre-commit 质量门禁。

**已有门禁**:
- `.pre-commit-config.yaml`: ruff 格式化
- `scripts/run_quality_gate.py`: compile/json/audit/pytest

**待添加门禁**:
1. **benchmark 回归测试**: 每次 commit 前自动跑关键 benchmark（Chara Dasha、Ashtakavarga、Transit），确保无精度退化。
2. **technique_registry 一致性检查**: 自动验证 registry 中引用的文件路径和命令确实存在。
3. **文档版本号同步检查**: 自动验证 `SKILL.md` / `CHANGELOG.md` / `README.md` 的版本号一致。

**验证方法**:
- 在 `.github/workflows/` 中添加 GitHub Actions workflow
- 测试: 故意提交一个破坏 Chara Dasha 的改动，验证 CI 拦截

---

### P3.4 开源项目持续监控

**目标**: 建立机制，定期扫描新出现的 Jyotish 开源项目，评估可复用性。

**当前已知项目库**:
- PyJHora (AGPL) — 算法参考金标准
- jyotishganit (MIT) — 已有 clone， strengths.py 可复用
- dashaflow (MIT) — 已适配合盘功能
- VedicAstro (MIT) — 完整 KP 系统
- vedic-calc (AGPL) — KP+Tajika+Prashna+Ashtakavarga
- vedic-astro-skills (MIT) — AI 解读 6 个 skill
- panchanga_api (开源) — 19 端点 REST API
- CNWU16/vedic-astro-skills (MIT, 161⭐) — AI 解读
- diliprk/VedicAstro (MIT, 63⭐) — 完整 KP
- rishi-ai-mcp — Sade Sati+Muhurtha+MCP 接入

**待监控渠道**:
- GitHub Topics: `jyotish`, `vedic-astrology`, `panchanga`
- PyPI 新包: `jyotish*`, `panchanga*`, `dasha*`
- arXiv: 印度占星相关算法论文

**验证方法**:
- 每季度手动或自动化扫描一次
- 新发现项目评估: 许可证、技术栈、可复用模块、精度声明

---

## 七、开源复用地图

| 目标模块 | 最佳开源来源 | 许可证 | 复用方式 | 当前状态 |
|----------|-------------|--------|---------|---------|
| Chara Dasha 共主判定 | PyJHora `_stronger_planet_new` | AGPL | 算法翻译 | 待执行 P0.1 |
| Vimshottari benchmark | PyJHora `vimsottari.py` | AGPL | 算法参考 | 待执行 P0.3 |
| PAV/Sodhita AV | PyJHora `ashtakavarga.py` | AGPL | 算法翻译 | 待执行 P0.4-P0.5 |
| Kakshya | PyJHora `kakshya.py` | AGPL | 算法翻译 | 待执行 P0.6 |
| Shadbala 完整版 | PyJHora `shad_bala.py` | AGPL | 算法翻译 | 待执行 P1.1 |
| jyotishganit strengths | jyotishganit `components/strengths.py` | MIT | 直接复用/适配 | 已有 clone |
| Bhava Chalit | PyJHora `chart.py` | AGPL | 算法翻译 | 待执行 P1.2 |
| Sudarshana Chakra | PyJHora `chart.py` | AGPL | 算法翻译 | 待执行 P1.3 |
| Tajika Yogas | PyJHora `tajika/yogas.py` | AGPL | 算法翻译 | 待执行 P1.4 |
| Sahams 36种 | PyJHora `tajika/saham.py` | AGPL | 算法翻译 | 待执行 P1.5 |
| Sade Sati 完整 | PyJHora `transit/sade_sati.py` | AGPL | 算法翻译 | 待执行 P1.6 |
| 高级分盘 D81+ | PyJHora `chart.py` | AGPL | 算法参考 | 待执行 P2.1 |
| Bhava Bala | PyJHora `bhava_bala.py` | AGPL | 算法翻译 | 待执行 P2.2 |
| 额外 Dasha | PyJHora `dhasa/*.py` | AGPL | 算法翻译 | 待执行 P2.3 |
| 分盘 Yoga | PyJHora `yoga.py` | AGPL | 算法参考 | 待执行 P2.4 |
| Transit 搜索 | PyJHora `transit.py` | AGPL | 算法参考 | 待执行 P2.5 |
| KP 完整系统 | VedicAstro (diliprk) | MIT | 直接复用/适配 | 未开始 |
| Prashna 完整 | vedic-calc (atolat) | AGPL | 算法参考 | 未开始 |

> **AGPL 复用原则**: 不直接复制代码到 MIT 仓库。阅读 AGPL 代码理解算法，用独立代码重新实现。在注释中标注算法来源和许可证。

---

## 八、验证策略总览

### 8.1 三层验证体系

| 层级 | 方法 | 适用 | 工具 |
|------|------|------|------|
| **L1 单元测试** | pytest + 不变量检查 | 每个函数 | `pytest tests/` |
| **L2 Benchmark** | PyJHora oracle 对比 | 每个核心模块 | `benchmarks/jyotish/scripts/` |
| **L3 集成验证** | full-reading 端到端 | 每次版本发布 | `scripts/jyotish_engine.py full-reading` |

### 8.2 Benchmark 通过标准

| 模块 | 通过标准 | 当前 | 目标 |
|------|---------|------|------|
| Chara Dasha | Overall ≥95% | 95.83% ✅ | ≥98% |
| Ashtakavarga | SAV=337/386 | ✅ | 保持 |
| Shadbala | 内部1200/1200 + 外部≤5%差异 | 内部✅ 外部❌ | 外部✅ |
| Transit | 340/340 Swiss匹配 | ✅ | 保持 |
| Yoga | F1 ≥95% | 95.22% ✅ | ≥96% |
| Vimshottari | 待建立 | — | ≥95% |

### 8.3 版本发布检查清单

- [ ] 所有 P0 任务 benchmark 通过
- [ ] `pytest tests/` 全通过
- [ ] `scripts/audit_capabilities.py --mode validate` 无错误
- [ ] `scripts/run_quality_gate.py` 无错误
- [ ] `SKILL.md` / `CHANGELOG.md` / `README.md` 版本号一致
- [ ] technique_registry.json 与实际代码状态一致
- [ ] GitHub 仓库已 push

---

## 九、诚实的能力评估

### 当前真实排名（纯技术，第8名左右）

| 排名 | 项目 | 领先点 |
|------|------|--------|
| 1 | PyJHora (AGPL) | 30+ Dasha、完整Shadbala、1000+ Yoga、全分盘 |
| 2 | vedic-calc (AGPL) | KP+Tajika+Prashna+Ashtakavarga 完整 |
| 3 | VedicAstro (MIT) | 完整KP系统、结构化数据 |
| 4 | jyotishganit (MIT) | 干净架构、完整测试 |
| 5 | panchanga-api (开源) | 19端点REST、300+ Yogas |
| 6 | dashaflow (MIT) | 多Dasha流、合盘 |
| 7 | vedic-astro-skills (MIT) | AI解读、6个skill |
| **8** | **yinduzhanxing (MIT)** | **中文AI解读层、技法审计系统、Yoga F1=95.22%、Chara Dasha 95.83%** |
| 9+ | 其他小项目 | — |

### 独特价值（不可替代性）

1. **中文AI解读层**: 全球唯一以中文为母语的 Jyotish AI 解读系统，覆盖从入门到专业的完整工作流。
2. **技法审计系统**: technique_registry + audit_capabilities + benchmark 的三层验证体系，确保每次解读的技法调用透明可审计。
3. **Yoga 精度**: F1=95.22% 在开源项目中属于第一梯队（PyJHora 未公开 Yoga 精度数据，但规则数更多）。
4. **模块化设计**: `jyotish_engine.py` 30+ 子命令 + `full-reading` 47 模块，结构清晰。

### 真实差距

1. **Dasha 系统**: 7种 vs PyJHora 30+ 种，差距显著。
2. **Shadbala 外部校准**: 内部一致但无绝对值对标，不能声称"完整"。
3. **分盘变体**: 只实现标准算法，无 Hora 6 变体、D3 4 变体等。
4. **Tajika 高级功能**: 缺 Panchavargiya Bala、Harsha Bala、完整 Sahams。
5. **Prashna 深度**: 缺 Sphuta、Trisphuta、数字选盘。
6. **社区与生态**: 0 Stars（GitHub），无外部贡献者，与 PyJHora 等成熟项目差距巨大。

---

*本文档基于 v6.1.12 代码实际状态编制，所有文件路径、函数名、指标均经过验证。优化方案按 P0→P1→P2→P3 顺序执行，不设定完成时间，以 benchmark 通过为唯一验收标准。*
