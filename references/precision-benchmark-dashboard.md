# Jyotish 精度基准仪表盘 v2.0

> 集中记录各技法的已知精度基准、工程门禁与改善进度。  
> 更新：2026-06-13 | 版本：v6.9.14

---

## 一、整体精度概览

| 维度 | 当前精度 / 状态 | 目标 | 评价 |
|------|----------------|------|------|
| 基础排盘（上升+日月星座） | **100%** (48/48) | 100% | ✅ 达标 |
| Yoga 检测（vs PyJHora） | **95.22% F1** | >95% | ✅ 达标 |
| Vimshottari Dasha 反推 | **~69%** | >85% | ⚠️ 下一阶段继续校准 Antardasha/Pratyantar |
| Chara Dasha 计算层 | **~95.25%** 加权匹配 | >95% | ✅ dignity bug 修复后达标 |
| Chara Dasha 解读层（KN Rao） | **24.17%** | >80% | 🔴 仍是最大精度缺口，问题不在 dignity 输出 bug |
| Double Transit | **70-85%** | >60% | ✅ Swiss Ephemeris 实时经度后达标 |
| DK Jupiter 婚姻激活 | **90-100%** | >80% + 降低虚高 | ⚠️ 命中高但覆盖面过宽 |
| Shadbala | **BPHS标准实现** | JHora 外部校准 | ✅ 内部规则完成，待更多外部样本 |
| KP Sub-Lord | **Sub/SubSub + ABCD Significator** | CSV Oracle稳定 | ✅ 已纳入测试 |
| Ashtakoot 合婚 | **36点+附加Kuta+Kuja** | 规则完整 | ✅ 完成 |
| Bhava Chalit | **Sripati/Porphyry/Equal/Whole/Placidus/Koch** | JHora标配 | ✅ v6.9.13 完成 |
| Sudarshana Chakra | **Asc/Moon/Sun 三参考点叠加** | BPHS标准分析 | ✅ v6.9.14 完成 |
| 测试门禁 | **475/475 pytest PASS** | 200+ | ✅ 超额完成 |
| 能力注册表审计 | **65项技法 validate PASS** | 0 missing/partial | ✅ 完成 |

---

## 二、分技法精度追踪

### 2.1 Vimshottari Dasha

| 测试 | 案例数 | 事件数 | 命中数 | 命中率 | 数据源 |
|------|--------|--------|--------|--------|--------|
| 事件应期反推 | 12 | 42 | ~29 | ~69% | smoke_test_runner |
| 婚姻支持 | 18 | 26 | ~18 | ~70% | marriage-timing-v6 |
| Antardasha / Pratyantar | — | — | — | 待扩展 | 下一阶段 |

**下一步**：从 Mahadasha 粗筛升级到 Antardasha / Pratyantar 精确窗口，并与 Transit 触发合并评分。

### 2.2 Chara Dasha (Jaimini)

| 层级 | 修复前 | 修复后 | 结论 |
|------|--------|--------|------|
| Sign 序列 | 100% | 100% | ✅ 序列没问题 |
| Duration 匹配 | 90.83% | 90.83% | ⚠️ 仍有 11/120 大幅偏差待查 |
| Dignity 检出率 | 0% | ~95% | ✅ dignity_adjustment bug 已修复 |
| 计算层加权匹配 | ~76.25% | **~95.25%** | ✅ 计算层达标 |
| KN Rao 解读层 | 24.17% | **24.17%** | 🔴 未改善，说明缺口在解释规则/事件映射层 |

**关键结论**：v6.9.10 修复的是输出字段 bug，不是 KN Rao 解读规则本身。真正下一步是补 KN Rao 事件映射规则、Rashi Dasha interpretation、Karaka/Arudha 联动，而不是继续改 dignity。

### 2.3 Double Transit (KN Rao)

| 测试 | 修复前 | 修复后 | 数据源 |
|------|--------|--------|--------|
| 真实过境经度 | mean-speed fallback | Swiss Ephemeris Lahiri | transit_trigger.py |
| 婚姻/事件触发 | 20-40% | **70-85%** | 内部回归 |
| 输出稳定性 | raw/interval 混用 | start_date/end_date 统一 | v6.9.13 |

### 2.4 Shadbala

| 组件 | 状态 | 说明 |
|------|------|------|
| Sthana Bala | ✅ | Ucha/Kendra/Ojhayugma 等规则完整 |
| Kendra Bala | ✅ | BPHS 三档：Kendra=60, Panapara=30, Apoklima=15 |
| Bhava Bala | ✅ | Adhipathi + Occupant + Aspect 评估 |
| Hora Bala | ✅ | 出生时主加权 |
| Chesta Bala | ✅ | Sun 使用 Seeghrochcha 速度映射 |
| JHora外部校准 | ⬜ | 仍需多案例人工对照 |

### 2.5 分盘 / Bhava / 三参考点

| 模块 | 状态 | 能力 |
|------|------|------|
| D2 Hora 变体 | ✅ | 6种：Parashara/Pariveshta/Parivritta/Parivritta-Trayodamsa/Surya-Chandra/Ahoratra |
| D3 Drekkana 变体 | ✅ | 4种：Parashara/Parivritta-Trayodamsa/Somaja/Khara |
| 复合分盘 | ✅ | D-m×n，例如 D9×D12=D108 |
| 自定义 D-N | ✅ | N=2-300，对齐 JHora 自定义分盘能力 |
| Bhava Chalit | ✅ | Rashi vs Bhava 偏移、宫头、Sandhi、移动行星汇总 |
| Sudarshana Chakra | ✅ | Asc/Moon/Sun 三盘、行星复合评分、12宫领域分析、收敛性 |

---

## 三、测试与质量门禁

| 门禁 | 当前结果 | 说明 |
|------|----------|------|
| pytest collect | **475 tests** | 20 个 test_*.py 文件 |
| pytest full suite | **475/475 PASS** | 2026-06-13 实测 |
| capability registry | **65 techniques PASS** | 0 problems / 0 warnings |
| CLI smoke | ✅ | chart/dasha/varga/ashtakavarga/audit-capabilities 等 |
| Bhava Chalit CLI | ✅ | `bhava-chalit --mode compare` 正常输出 |
| Sudarshana CLI | ✅ | `sudarshana --house 10` 正常输出 |
| 安全扫描 | ✅ | Git 跟踪文件未发现高风险密钥 |

新增/修复测试重点：
- `tests/test_bhava_chalit.py`
- `tests/test_sudarshana_chakra.py`
- `tests/test_divisional_charts_extended.py`
- `tests/test_ashtakoot.py`
- `tests/test_tajika.py`
- `tests/test_shadbala_complete.py`
- `tests/test_transit_complete.py`
- `tests/test_nakshatra.py`

---

## 四、P0/P1 路线图

### P0 — 已闭合

1. [x] PyPI/Docker/CI 配置就位（不打 tag，不发布）
2. [x] PDF报告输出
3. [x] 精度回归测试框架 + MEVG 门控
4. [x] Transit Swiss Ephemeris 精度升级
5. [x] KP 完整系统 + Oracle 测试
6. [x] Shadbala 精度升级
7. [x] Ashtakoot 36点合婚
8. [x] 10个 partial 技法升级 complete
9. [x] 分盘变体 + 复合分盘 + 自定义 D-N
10. [x] Bhava Chalit 完整化
11. [x] Sudarshana Chakra 完整化
12. [x] 测试覆盖 200+ 目标超额完成（475）
13. [x] 能力注册表 65项审计通过

### P1 — 下一阶段建议

1. [ ] Chara Dasha 解读层：24.17% → 80%（当前最大精度缺口）
2. [ ] Vimshottari Antardasha/Pratyantar 事件窗口校准：~69% → 85%+
3. [ ] JHora 外部校准集：Shadbala/Bhava Chalit/Varshaphala 至少 5-10 公开案例
4. [ ] 事件数据集扩充：12名人/42事件 → 30+案例/100+事件
5. [ ] Full-reading 输出置信度模型：把 Chara、Vimshottari、Transit、KP、Sudarshana 收敛为统一评分

---

## 五、竞品差距重评估

| 竞品 | 强项 | 当前差距 | 策略 |
|------|------|----------|------|
| JHora | 闭源金标准、计算广度、用户信任 | 外部校准样本仍不足 | 不复制桌面计算器路线，重点做 AI可信解读 |
| PyJHora | 7,678测试、计算广度、AGPL积累 | 测试数量仍少，但核心门禁已补齐 | 继续用公开案例做精度对照，不走 AGPL 复制路线 |
| VedAstro | API/MCP/Docker/多端生态 | 社区/生态规模 | 用户明确暂不管社区；工程配置已追平一部分 |
| yinduzhanxing | 中文AI解读、MEVG审计、Technique Audit Table、开源FOSS | Chara解读层、事件数据集 | 保持“AI原生可信解读系统”差异化 |

**当前评分估算**：7.5 → **8.1/10**  
理由：工程化、测试、Bhava/Sudarshana/分盘变体补齐后，非社区维度明显前进；扣分主要来自 Chara Dasha 解读层 24.17% 与事件数据集规模。

---

## 六、当前一句话结论

社区先不管的前提下，项目已经从“功能很多但 partial/测试薄弱”推进到“核心技法 complete + 475测试门禁 + 能力审计通过”。现在真正拖后腿的不是工程化，而是 **Chara Dasha 解读层与事件级应期统计样本**。
