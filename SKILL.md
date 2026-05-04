---
name: jyotish-vedic-astrology
version: 6.0.0
description: 印度占星（Jyotish）专业解盘与推运系统。核心能力：PDF星盘输入→严谨解盘→精确推运应期输出。触发词：印度占星、吠陀占星、Jyotish、解盘、推运、星盘分析、Dasha、Transit、Nakshatra、Yoga、出生时间矫正、PDF星盘、读取PDF、分析PDF星盘、现代解读、误判纠错、Varga分盘、综合分析、过境分析、合盘、婚姻匹配、年运盘、Prashna、Argala、Jaimini、KP系统、Shadbala、Ashtakavarga、HTML报告、深度解盘。
---

# 印度占星专业解盘与推运系统

> **执行总控**：`references/quick-reference-guide.md`（⭐推荐优先阅读）
> **版本**：v6.0.0 | **详细变更**：`CHANGELOG.md`

---

## ⚠️ 核心定位

**三种输入 → 严谨解盘 → 精确推运应期输出**

| 路径 | 用户输入 | AI行为 |
|------|---------|--------|
| **A：精准出生信息** | 日期+时间+地点 | `full-reading` 引擎全链路计算 |
| **B：PDF/文字星盘** | PDF/详细文字描述 | 提取数据+Quality Gate → `references/pdf-chart-reading-guide.md` |
| **C：时间不明确** | "不知道几点出生" | 互动式出生时间矫正 → 确认后走路径A |

**强制工作流**（完整规范 → `references/ai-reading-workflow-prompt.md` v3.0）：

1. **阶段零**：入口路由（A/B/C自动判断）
2. **阶段一**（仅B）：PDF/图片提取 + Quality Gate
3. **阶段二**：意图识别 → 路由目标宫位（无明确意图→Level 2综合解盘）
4. **阶段三**：静态分析10步（宫位→承诺→Yoga→Argala→逆行→NK→Shadbala→AV→Ketu→分盘）
5. **阶段四**：动态推运7步（Dasha→Convergence→Transit→Double Transit→Jaimini→KP→Varshaphala）
6. **阶段五**：应期输出（五层验证→时间窗口→Actionable Output+案例检索）
7. **阶段六**：补救措施（可选）
8. **阶段七**：现代措辞包装

---

## ⚠️ 强制规则（与"不跳步"同级）

### MEVG 强制外部验证门控（v4.2.0+）

**所有解读结论必须经过外部权威来源验证，禁止仅凭 AI 训练记忆输出。**

| 门控 | 位置 | 职责 |
|------|------|------|
| Step 3.11 | 静态分析后 | 验证 Yoga/尊严/Shadbala/SAV |
| Step 4.10 | 动态推运后 | 验证 Transit/Dasha/天文现象 |
| Step 5.5 | 预测输出前 | 确认每条预测有来源+置信度一致 |

**三步验证法**：V1 构建英文查询词 → V2 web_search ≥3个独立来源 → V3 交叉验证仲裁分歧

→ 完整协议：`references/mandatory-verification-gate-protocol.md`

### Transit Actionable Output（v4.1.0+）

**每条 Transit 预测必须输出三要素**：
1. **时间段**（精确到日/周/月）
2. **具体行动类型**（做什么）
3. **置信度** [A]=已验证 / [B]=高概率(3+维度) / [C]=推断(单一维度)

→ 完整规范：`references/transit-actionable-output-guide.md`

---

## 核心能力速查

> 详细说明和参考文件索引 → `references/quick-reference-guide.md`

| 能力域 | 核心内容 | 主要参考文件 |
|--------|---------|------------|
| **静态分析** | 行星配置、Yoga、NK、宫位、Argala、Shadbala、AV、Badhaka、Raman方法论 | `planets.md` `yoga_list.md` `argala-complete-guide.md` `badhaka-obstacle-planet-guide.md` `raman-house-judgment-methodology.md` |
| **动态推运** | Vimshottari、Chara Dasha、KP、Double Transit、Varshaphala、替代Dasha | `vimshottari_dasha_guide.md` `dasa-convergence-methodology.md` `alternative-dasha-systems.md` |
| **关系占星** | Koota 36分、D9伴侣、DK、Mangal Dosha、配偶六层确认、高地位配偶Yoga | `spouse-multi-layer-methodology.md` `darakaraka-complete-guide.md` `marc-boney-marriage-six-step.md` |
| **出生时间矫正** | 八大方法、自动化流程、验证报告 | `birth-time-rectification-advanced.md` |
| **PDF读取** | JH/PL PDF全量提取、完整性门、交叉校验 | `pdf-chart-reading-guide.md` `data-bridge-mapping.md` |
| **Prashna问事** | 十步断卦、AL、Sphuta、Sahams、失物查询 | `prashna-complete-guide.md` `single-event-inquiry-protocol.md` |
| **多元技法** | Yogi/Ava Yogi、Tithi Lord、Rashi Tulya Navamsa、BCP、Pancha Pakshi | `yogi-avayogi-system.md` `tithi-lord-relationship-system.md` `bhrigu-chakra-paddhati.md` |
| **精准方法论** | PACDARES框架、九层复合方法、L3矛盾检查、三级置信度 | `precision-reading-methodology.md` |
| **现代解读** | 现代措辞映射、现代生活场景、常见误判纠错 | `modern-language-guide.md` `common-misconceptions.md` |

---

## 计算引擎

**统一入口**：`scripts/jyotish_engine.py`（基于 Swiss Ephemeris）

```bash
PYTHON=python3
SCRIPT=~/.workbuddy/skills/jyotish-vedic-astrology/scripts/jyotish_engine.py
$PYTHON $SCRIPT <子命令> [参数]
```

### 27大子命令速查

| 子命令 | 功能 |
|--------|------|
| `full-reading` | ⭐全自动综合解盘（13模块一键出） |
| `chart` | 星盘计算+`--validate`附加R1-R10验证 |
| `dasha` | Vimshottari大运时间线+小运展开 |
| `yoga` | Yoga格局识别 |
| `predict` | 三层验证法事件预测+`--past-verify`验前事 |
| `varga` | 分盘计算（D9/D10等） |
| `varga-full` | BPHS十六分盘精确计算（D2-D60） |
| `celebrity` | 名人案例查询 |
| `db-stats` | 验证数据库统计 |
| `transit` | 行星过境查询 |
| `shadbala` | 六重力量计算 |
| `ashtakavarga` | 八分法计算（SAV=337） |
| `memory` | Hermes记忆系统 |
| `validate` | R1-R10数学验证 |
| `audit` | P1-P12行星审计管线 |
| `aspects` | 度数精确相位系统 |
| `jaimini` | Jaimini完整系统+`--antardasha` |
| `nakshatra-adv` | 高级Nakshatra（Tara Bala+Sub-Lord） |
| `argala` | Argala门闩系统 |
| `tajika` | Tajika年运盘（Muntha+YearLord+Mudda Dasha） |
| `synastry` | 合盘分析（Ashta Koota 36分） |
| `report` | MD→HTML报告生成（羊皮纸主题） |
| `prashna` | Prashna问事占星 |
| `double-transit-pac` | KN Rao Double Transit PAC+D9层 |
| `transit-ll7l` | Transit LL/7L连接+互换 |
| `planetary-congregation` | 行星聚集检测 |
| `vivah-saham` | Vivah Saham婚姻敏感点 |

→ 完整参数和示例 → `references/quick-reference-guide.md`

---

## 核心方法论

### 三层验证法
1. **本命征象**：静态星盘中的征象
2. **大运激活**：Dasha系统激活相关宫位
3. **过境触发**：Transit系统触发具体事件（⚠️必须多参考点检查）

### 精准解盘方法论（v3.12.1）

**六大共识原则**：功能吉凶因盘而异 | 单一技法不做结论 | 规则前提先查 | 案例验证>经典引述 | 先整体后细节 | 先验证过去再预测未来

**PACDARES框架**：P位置→A相位→C合相→D财富Yoga→A灾厄Yoga→R皇家Yoga→E互换→S特殊

**九层复合方法**：L1 PACDARES → L2 分盘 → L3 矛盾检查(关键) → L4 Vimshottari → L5 AV+Transit → L6 条件Dasha → L7 Jaimini → L8 其他Jaimini → L9 Tajika

**三级置信度**：✅[A]已验证 / ⭐[B]强推断(3+维度) / ⚡[C]假设(单一维度)

→ 详见 `references/precision-reading-methodology.md`

---

## 强制规范速查

| 规范 | 版本 | 核心要求 | 参考文件 |
|------|------|---------|---------|
| MEVG外部验证 | v4.2.0 | 所有解读必须web_search验证 | `mandatory-verification-gate-protocol.md` |
| Transit Actionable | v4.1.0 | 预测必须输出时间段+行动+置信度 | `transit-actionable-output-guide.md` |
| 过境多参考点 | v1.9.0 | Lagna+Chandra Lagna双参考点(强制) | `transit-multi-reference-guide.md` |
| Ketu双属性 | v2.0.0 | 必须同时评估"放手"和"突破" | `ketu-dual-nature-guide.md` |
| Shadbala完整 | v2.0.0 | 六种力量全部评估 | `shadbala-complete-methodology.md` |
| Yoga Phala Timing | v2.1.0 | 识别Yoga后必须预测何时发生 | `yoga-phala-timing-guide.md` |
| 逆行/燃烧/战争 | v2.1.0 | 每颗行星检查三重叠加 | `retrograde-combustion-war-guide.md` |
| 精准方法论 | v3.12.1 | PACDARES+九层+L3矛盾检查 | `precision-reading-methodology.md` |

---

## 预测清单

- [ ] **MEVG-静态门控**：所有静态解读声明必须web_search验证
- [ ] 静态星盘分析（行星配置、Yoga、Nakshatra、宫位）
- [ ] Argala检查（2/4/5/8/11宫干预+Virodha）
- [ ] 逆行/燃烧/行星战争检查（三重叠加）
- [ ] Shadbala评估（六种力量完整评估）
- [ ] Ashtakavarga评估（BAV+SAV聚合校验337点）
- [ ] Ketu双重属性检查
- [ ] **MEVG-动态门控**：Transit/Dasha/天文现象必须验证
- [ ] Dasha推运（大运+小运+Pratyantar）
- [ ] Dasa Convergence三系统交叉验证
- [ ] Jaimini分析（Karaka+Chara Dasha）
- [ ] KP系统分析（Significator+Sub-Lord）
- [ ] Transit分析（多参考点强制）
- [ ] **Transit Actionable Output**（时间段+行动+置信度+案例检索）
- [ ] 分盘验证
- [ ] 预测边界检查（置信度标注，禁止绝对断言）
- [ ] **案例检索**：动态预测必须先检索真实案例
- [ ] **MEVG-预测门控**：确认每条预测有来源+置信度一致

---

## 参考资料索引

> 完整描述和版本信息 → `references/quick-reference-guide.md` §参考资料完整索引

共 **105个文件**，按功能分组：

| 分组 | 数量 | 核心文件 |
|------|------|---------|
| AI工作流 | 2 | `ai-reading-workflow-prompt.md` ⭐ `quick-reference-guide.md` ⭐ |
| 核心方法论 | 9 | `common-misconceptions.md` `modern-language-guide.md` `pdf-chart-reading-guide.md` `prediction-boundary-protocol.md` |
| 基础知识 | 7 | `planets.md` `signs-and-houses.md` `nakshatra_deities.md` `vimshottari_dasha_guide.md` |
| Yoga体系 | 5 | `yoga_list.md` `neechabhanga-raja-yoga.md` `yoga-phala-timing-guide.md` |
| 宫位/场景 | 3 | `house-modern-mapping.md` `house-domain-planet-mapping.md` |
| 占星系统 | 5 | `jaimini-complete-system.md` `kp-astrology-complete-system.md` `remedies-complete-system.md` |
| 分盘/力量 | 7 | `ashtakavarga-complete-system.md` `shadbala-complete-methodology.md` `shodasavarga-complete-guide.md` |
| 过境/推运 | 9 | `transit-comprehensive-guide.md` `dasa-convergence-methodology.md` `alternative-dasha-systems.md` |
| 关系占星 | 5+ | `spouse-multi-layer-methodology.md` `darakaraka-complete-guide.md` `marc-boney-marriage-six-step.md` |
| 综合框架 | 5 | `comprehensive-reading-workflow.md` `deep-analysis-complete-workflow.md` |
| 高级技法 | 5 | `advanced-techniques.md` `global-astrologer-practical-methodology.md` |
| 案例库 | 13 | `famous-case-library.md` `verified-celebrity-cases.md` |
| 多元技法 | 5 | `yogi-avayogi-system.md` `bhrigu-chakra-paddhati.md` `pancha-pakshi-nakshatra-systems.md` |
| BPHS/Raman/Goel | 5 | `badhaka-obstacle-planet-guide.md` `raman-house-judgment-methodology.md` `vp-goel-jaimini-dasha-systems.md` |
| MEVG | 1 | `mandatory-verification-gate-protocol.md` |

---

## 注意事项

1. **出生时间精度**：±2分钟内最佳，可通过矫正提高
2. **三层验证法**：所有预测必须Dasha+Transit+Varga交叉验证
3. **现代场景优先**：所有解读使用现代措辞和现代生活场景映射
4. **解盘深度**：默认Level 2（专项），复杂问题自动升级Level 3
5. **不凭记忆**：禁止仅凭AI训练记忆输出解读结论，必须MEVG验证

---

**版本**：6.0.0
**创建日期**：2026-04-20
**最后更新**：2026-05-04（v6.0.0 架构重构：SKILL.md精简86KB→~25KB+quick-reference-guide升级为执行总控+dignity土星MT修正+月亮/水星多学派加注+dasha_guide余数规则修正）
