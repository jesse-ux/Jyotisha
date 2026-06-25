# 印度占星技法完整覆盖度地图
# Jyotish Vedic Astrology — Complete Technique Coverage Map

> 版本: v1.0 | 日期: 2026-06-07
> 基于 yinduzhanxing Python引擎 + jyotish-app 前端引擎 全面审计

---

## 一、审计方法论

### 1.1 技法分类体系

印度占星技法按**分析维度**分为6大体系：

| 体系 | 英文 | 作用 |
|------|------|------|
| 本命分析 | Natal Analysis | 解读出生星盘，描述先天格局 |
| 推运系统 | Dasha Systems | 时间周期，何时发生 |
| 流年系统 | Transit/Gochara | 行星过境，具体触发 |
| 择时系统 | Muhurta/Electional | 选择吉时 |
| 问事系统 | Prashna/Horary | 针对具体问题 |
| 合盘系统 | Synastry/Compatibility | 两人关系匹配 |

每个体系下按**技法层级**分为4级：

| 层级 | 名称 | 说明 |
|------|------|------|
| L1 | 基础计算 | 星盘排盘、宫位、行星位置 |
| L2 | 标准技法 | 主流教科书必讲的技法 |
| L3 | 高级技法 | 专业占星师使用，需额外学习 |
| L4 | 秘传技法 | 师徒口传，经典中隐含 |

### 1.2 状态标记

| 标记 | 含义 | 说明 |
|------|------|------|
| ✅ | 已完备 | 计算+解读+验证完整 |
| ⚠️ | 部分完成 | 有计算但缺深度解读，或验证不足 |
| ❌ | 缺失 | 完全没有实现 |
| 🔧 | 待优化 | 有实现但精度或覆盖度需提升 |

---

## 二、本命分析体系 (Natal Analysis)

### 2.1 上升系统 (Lagna Systems)

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Udaya Lagna (上升星座)** | ✅ | jyotish_engine.py | 核心，精确到秒 |
| **Chandra Lagna (月亮上升)** | ✅ | jyotish_engine.py | 以月亮星座为第1宫 |
| **Surya Lagna (太阳上升)** | ⚠️ | 隐含在chart中 | 以太阳星座为第1宫，无专门分析 |
| **Karakamsha (AK星座)** | ⚠️ | jaimini.py | 有计算，解读模板化 |
| **Arudha Lagna (镜像上升)** | ✅ | special_lagnas.py | 完整计算 |
| **Arudha Padas (各宫镜像)** | ⚠️ | special_lagnas.py | 1-12宫Arudha，解读不足 |
| **Upapada Lagna (婚姻上升)** | ⚠️ | special_lagnas.py | 有计算，无深度解读 |
| **Bhava Lagna (宫位上升)** | ❌ | — | 未实现 |
| **Ghati Lagna (时升)** | ❌ | — | 未实现 |
| **Hora Lagna (日升)** | ❌ | — | 未实现 |
| **Vighati Lagna (分升)** | ❌ | — | 未实现 |
| **Pranapada Lagna (息升)** | ❌ | — | 未实现 |
| **Indu Lagna (月升)** | ❌ | — | 未实现 |
| **Sree Lagna (财升)** | ❌ | — | 未实现 |

**覆盖度: 5/14 = 36%**

### 2.2 象征系统 (Karaka Systems)

#### 2.2.1 Sthira Karaka (固定象征)

| 技法 | 状态 | 说明 |
|------|------|------|
| 7大固定象征 | ✅ | Sun=灵魂, Moon=心智, Mars=兄弟, Mercury=亲戚, Jupiter=子女, Venus=配偶, Saturn=长寿 |
| 8大固定象征 (含Rahu/Ketu) | ⚠️ | Rahu=祖父, Ketu=祖母，部分实现 |

#### 2.2.2 Chara Karaka (可变象征)

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **7星Chara Karaka计算** | ✅ | jaimini.py | 完整 |
| **8星Chara Karaka计算** | ✅ | jaimini.py | 完整，含Rahu逆行校正 |
| **Atmakaraka (AK)解读** | ⚠️ | karaka_calculator.py | 有计算，解读不足 |
| **Amatyakaraka (AmK)解读** | ⚠️ | karaka_calculator.py | 有计算，解读不足 |
| **Bhratrukaraka (BK)解读** | ⚠️ | karaka_calculator.py | 有计算，解读不足 |
| **Matrukaraka (MK)解读** | ⚠️ | karaka_calculator.py | 有计算，解读不足 |
| **Putrakaraka (PK)解读** | ⚠️ | karaka_calculator.py | 有计算，解读不足 |
| **Gnatikaraka (GK)解读** | ⚠️ | karaka_calculator.py | 有计算，解读不足 |
| **Darakaraka (DK)深度解读** | ❌ | — | **6大缺失模块之一** |
| **Pitrukaraka (PiK)** | ❌ | — | 8星系统第8颗，未实现 |
| **Karakamsha解读** | ⚠️ | jaimini.py | 有基础解读 |

**覆盖度: 4/11 = 36% (计算完备，解读不足)**

#### 2.2.3 Naisargika Karaka (自然象征)

| 技法 | 状态 | 说明 |
|------|------|------|
| 标准自然象征 | ✅ | 已内置 |

### 2.3 分盘系统 (Varga/Divisional Charts)

| 分盘 | 名称 | 主题 | 状态 | 说明 |
|------|------|------|------|------|
| **D1** | Rashi | 本命/general | ✅ | 完整 |
| **D2** | Hora | 财富 | ✅ | 完整 |
| **D3** | Drekkana | 兄弟姐妹/勇气 | ✅ | 完整 |
| **D4** | Chaturthamsa | 房产/车辆/幸福 | ✅ | 完整 |
| **D7** | Saptamsa | 子女/后代 | ✅ | 完整 |
| **D9** | Navamsa | 婚姻/dharma/果实 | ✅ | 完整计算 |
| **D10** | Dashamsa | 事业/行动 | ✅ | 完整 |
| **D12** | Dwadasamsa | 父母/祖先 | ✅ | 完整 |
| **D16** | Shodasamsa | 车辆/舒适/苦难 | ✅ | 完整 |
| **D20** | Vimsamsa | 灵性/宗教 | ✅ | 完整 |
| **D24** | Chaturvimsamsa | 教育/学问 | ✅ | 完整 |
| **D27** | Saptavimsamsa | 力量/体能 | ✅ | 完整 |
| **D30** | Trimshamsa | 不幸/邪恶/疾病 | ✅ | 完整 |
| **D40** | Khavedamsa |  auspicious acts | ✅ | 完整 |
| **D45** | Akshavedamsa | 性格/品质 | ✅ | 完整 |
| **D60** | Shashtiamsa | 一般指示/业力 | ✅ | 完整 |
| **D81** | Navamsa-Navamsa | D9之D9精微分盘 | ✅ | 已实现并纳入扩展分盘 |
| **D108** | Dwadasamsa-Navamsa | D12之D9精微分盘 | ✅ | 已实现并纳入扩展分盘 |
| **D144** | Dwadasamsa-Dwadasamsa | D12之D12精微分盘 | ✅ | 已实现并纳入扩展分盘 |
| **D150** | — | 更精微 | ❌ | 未实现 |

**覆盖度: 19/20 = 95%（分盘计算层；深度解读模板仍集中在 D24/D30/D60 等重点分盘）**

### 2.4 分盘映射技法 (Varga Mapping)

| 技法 | 状态 | 说明 |
|------|------|------|
| **Vargottama (同星座分盘)** | ✅ | D1和D9同星座 |
| **Rashi Tulya Navamsa (RTN)** | ✅ | v6.1.10 已接入 full-reading |
| **Navamsa Tulya Rashi** | ❌ | RTN反向 |
| **Rashi Tulya Dashamsa** | ❌ | D10映射 |
| **Rashi Tulya Trimshamsa** | ❌ | D30映射 |
| **Karakamsha Navamsa分析** | ⚠️ | 有计算，解读不足 |

**覆盖度: 1/6 = 17%**

### 2.5 力量评估系统 (Strength Assessment)

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Shadbala (六重力量)** | ✅ | shadbala.py | Sthana/Dig/Kala/Chesta/Naisargik/Drik |
| **Vimsopaka Bala (20分力量)** | ✅ | vimsopaka_calculator.py | 完整 |
| **Vaiseshikamsa (特殊分)** | ✅ | vimsopaka_calculator.py | 完整 |
| **Ishta Phala (吉祥果)** | ❌ | — | 未实现 |
| **Kashta Phala (凶险果)** | ❌ | — | 未实现 |
| **Drik Bala (相位力量)** | ⚠️ | shadbala.py | 部分实现 |
| **Chesta Bala (运动力量)** | ⚠️ | shadbala.py | 部分实现 |
| **Kendra Bala (角宫力量)** | ❌ | — | 未实现 |
| **Uchcha Bala (高行力量)** | ❌ | — | 未实现 |
| **Moolatrikona Bala (本宫力量)** | ❌ | — | 未实现 |
| **Oja-Yugma Bala (奇偶力量)** | ❌ | — | 未实现 |
| **Paksha Bala (月相力量)** | ❌ | — | 未实现 |
| **Tribhaga Bala (三分力量)** | ❌ | — | 未实现 |
| **Nathonnata Bala (升降力量)** | ❌ | — | 未实现 |
| **Yuddha Bala (战争力量)** | ❌ | — | 未实现 |

**覆盖度: 3/15 = 20%**

### 2.6 行星状态系统 (Planetary States)

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Dignity (庙旺落陷)** | ✅ | jyotish_engine.py | 庙旺/落陷/本宫/友好/中立/敌对/ detriment |
| **Combustion (燃烧)** | ✅ | jyotish-advanced.js | 前后8-15度 |
| **Retrograde (逆行)** | ✅ | jyotish_engine.py | 完整 |
| **Avasthas (行星状态)** | ✅ | avastha_calculator.py | Baladi/Sayan/... 10+状态 |
| **War (行星战争)** | ⚠️ | 部分 | 有概念，无系统检测 |
| **Planetary Conjunction Effects** | ⚠️ | yoga_engine | 部分覆盖 |
| **Old/Infant (老幼)** | ⚠️ | avastha中 | 部分 |
| **Planetary Directions** | ❌ | — | 未实现 |

**覆盖度: 5/8 = 63%**

### 2.7 Yoga组合系统

| 技法 | 状态 | 说明 |
|------|------|------|
| **Raja Yogas (王组合)** | ✅ | 476条规则，F1=93.8% |
| **Dhana Yogas (财组合)** | ✅ | 包含在476条中 |
| **Arista Yogas (凶组合)** | ✅ | 包含在476条中 |
| **Nabhasa Yogas (天象组合)** | ✅ | 包含在476条中 |
| **Marriage Yogas (婚姻组合)** | ⚠️ | 部分覆盖 |
| **Career Yogas (事业组合)** | ⚠️ | 部分覆盖 |
| **Spiritual Yogas (灵性组合)** | ⚠️ | 部分覆盖 |
| **Curse Yogas (凶星合相命名)** | ❌ | **6大缺失模块之一** |
| **High-Status Spouse Yoga** | ❌ | **6大缺失模块之一** |
| **Neecha Bhanga Raja Yoga** | ⚠️ | 有文档，检测待优化 |
| **Parivartana Yoga (互换)** | ✅ | 已实现 |
| **Vipareeta Raja Yoga** | ✅ | 已实现 |
| **Dharma-Karmadhipati Yoga** | ✅ | 已实现 |
| **Sreenatha Yoga** | ❌ | 未实现 |
| **Chamara Yoga** | ❌ | 未实现 |
| **Sata Yuga / Treta Yuga 等** | ❌ | 未实现 |

**覆盖度: 10/16 = 63%**

### 2.8 相位系统 (Aspects/Drishti)

| 技法 | 状态 | 说明 |
|------|------|------|
| **Graha Drishti (行星相位)** | ✅ | aspects.py | 7行星特殊相位 |
| **Rasi Drishti (星座相位)** | ✅ | aspects.py | 同象星座相位 |
| **Special Drishti (特殊相位)** | ⚠️ | 部分 | Rahu/Ketu特殊相位 |
| **Aspect Strength (相位力量)** | ⚠️ | 部分 | 未完整量化 |
| **Mutual Aspect (互相位)** | ✅ | 已实现 |
| **Aspect by Lord (宫主相位)** | ✅ | 已实现 |

**覆盖度: 4/6 = 67%**

### 2.9 宫位系统 (Bhavas)

| 技法 | 状态 | 说明 |
|------|------|------|
| **Bhava Calculation (宫位计算)** | ✅ | Sripathi/Koch等 |
| **Bhava Lords (宫主星)** | ✅ | 完整 |
| **Bhava Sandhi (宫位交界)** | ⚠️ | 部分 |
| **Chalit Chart (变动宫位)** | ⚠️ | 部分 |
| **PAC-DARES** | ✅ | analysis-deep.py | 专业级 |
| **House Influence Scoring** | ✅ | analysis-deep.py | Raman评分 |
| **Bhavat Bhavam (宫的宫)** | ⚠️ | 隐含 | 未系统化 |

**覆盖度: 5/7 = 71%**

### 2.10 星宿系统 (Nakshatras)

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Nakshatra计算** | ✅ | jyotish_engine.py | 27星宿精确计算 |
| **Pada计算** | ✅ | jyotish_engine.py | 108分Quarter |
| **Nakshatra Deity** | ✅ | references/nakshatra_deities.md | 完整 |
| **Tara Bala** | ✅ | nakshatra_advanced.py | 9种Tara |
| **Nakshatra Compatibility** | ✅ | nakshatra_advanced.py | 28分体系 |
| **Yoni Kuta** | ✅ | synastry.py | 合盘中使用 |
| **Gana Kuta** | ✅ | synastry.py | 合盘中使用 |
| **Nadi Kuta** | ✅ | synastry.py | 合盘中使用 |
| **Nakshatra Dasha Lords** | ✅ | dasha_calculator.py | Vimshottari基础 |
| **Nakshatra Symbolism** | ⚠️ | references中 | 有文档，未结构化 |

**覆盖度: 9/10 = 90%**

### 2.11 Argala系统 (Obstructions & Interventions)

| 技法 | 状态 | 说明 |
|------|------|------|
| **Argala计算** | ✅ | argala.py | 2/4/11宫助力 |
| **Virodhargala计算** | ✅ | argala.py | 12/10/3宫阻碍 |
| **Argala解读** | ⚠️ | 有文档 | 未深度结构化 |

**覆盖度: 2/3 = 67%**

### 2.12 其他本命技法

| 技法 | 状态 | 说明 |
|------|------|------|
| **Sudarshana Chakra** | ❌ | 未实现 |
| **Sahams (阿拉伯点)** | ⚠️ | tajika.py中部分 | 婚姻Saham有 |
| **Gulika/Mandi** | ⚠️ | prashna.py中 | 有计算 |
| **Upagraha (副星)** | ⚠️ | prashna.py中 | 部分 |
| **Pranapada** | ❌ | 未实现 |
| **Hora Chart Analysis** | ⚠️ | 有计算，无解读 |
| **Trisphuta** | ❌ | 未实现 |

**覆盖度: 1/7 = 14%**

---

## 三、推运系统 (Dasha Systems)

### 3.1 主要Dasha系统

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Vimshottari Dasha** | ✅ | dasha_calculator.py | 120年周期，精确计算 |
| **Antardasha (Bhukti)** | ✅ | dasha_calculator.py | 二级推运 |
| **Pratyantardasha** | ✅ | dasha_calculator.py | 三级推运 |
| **Sookshma/Prana Dasha** | ⚠️ | dasha_calculator_enhanced.py | 四五级 |
| **Ashtottari Dasha** | ✅ | ashtottari_dasha.py | v6.1.10 已实现 |
| **Yogini Dasha** | ❌ | — | 未实现 |
| **Jaimini Chara Dasha** | ✅ | jaimini.py | v6.1.12 KN Rao Method, benchmark 95.83% |
| **Sthira Dasha** | ❌ | — | 未实现 |
| **Kalachakra Dasha** | ❌ | — | 未实现 |
| **Narayana Dasha** | ❌ | — | 未实现 |
| **Moola Dasha** | ❌ | — | 未实现 |
| **Shasti-Hayani Dasha** | ❌ | references中有文档 | 未实现 |
| **Bhrigu Chakra Paddhati** | ⚠️ | references中有文档 | 未实现计算 |
| **Bhrigu Pada Dasha** | ⚠️ | references中有文档 | 未实现计算 |
| **Conditional Dasha** | ❌ | references中有文档 | 未实现 |
| **Tara Dasha** | ❌ | — | 未实现 |
| **Kendradi Dasha** | ❌ | — | 未实现 |
| **Navamsa Dasha** | ❌ | — | 未实现 |

**覆盖度: 4/18 = 22%**

### 3.2 Dasha分析技法

| 技法 | 状态 | 说明 |
|------|------|------|
| **Dasha主题分析** | ✅ | dasha_analyzer.py | 事件主题 |
| **Dasha + Transit联动** | ✅ | dasha_calculator_enhanced.py | 部分 |
| **Multi-Dasha Convergence** | ⚠️ | references中有文档 | 未系统化 |
| **Dasha Sandhi (交界期)** | ⚠️ | 部分 | 未深度分析 |
| **Yoga Phala Timing** | ⚠️ | references中有文档 | 未系统化 |
| **Bhrigu Nadi Method** | ❌ | — | 未实现 |

**覆盖度: 3/6 = 50%**

---

## 四、流年系统 (Transit/Gochara)

### 4.1 基础Transit

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Planetary Transit计算** | ✅ | transit.py | 精确计算 |
| **Transit Overlay** | ✅ | transit.py | 过境叠加 |
| **Double Transit** | ✅ | jyotish_engine.py | KN Rao体系 |
| **PAC in Transit** | ✅ | jyotish_engine.py | 完整 |
| **Sade Sati** | ✅ | transit.py | 土星7.5年 |
| **Kantaka Shani** | ❌ | — | 未实现 |
| **Ashtama Shani** | ❌ | — | 未实现 |
| **Kakshya (宫位区间)** | ❌ | — | 未实现 |
| **Ashtakavarga Transit** | ⚠️ | transit.py | 部分 |
| **Gochara (本命宫Transit)** | ⚠️ | 部分 | 未完整 |

**覆盖度: 6/10 = 60%**

### 4.2 高级Transit技法

| 技法 | 状态 | 说明 |
|------|------|------|
| **Transit + LL/7L连接** | ✅ | jyotish_engine.py | 婚姻预测 |
| **Planetary Congregation** | ✅ | jyotish_engine.py | 行星聚集 |
| **Vivah Saham + Transit** | ✅ | jyotish_engine.py | 婚姻Saham |
| **Transit Actionable Output** | ✅ | references中有指南 | 结构化输出 |
| **Vedha (遮挡)** | ❌ | — | 未实现 |
| **Tara Bala in Transit** | ⚠️ | 部分 | 未完整 |

**覆盖度: 4/6 = 67%**

---

## 五、择时系统 (Muhurta/Electional)

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Panchanga (五支)** | ⚠️ | 隐含 | Tithi/Nakshatra/Yoga/Karana |
| **Tithi Analysis** | ❌ | — | **6大缺失模块之一** |
| **Tithi Lord** | ❌ | references中有文档 | 未实现计算 |
| **Tithi Yoga** | ⚠️ | jyotish-advanced.js | 部分 |
| **Nakshatra Selection** | ⚠️ | 部分 | Tara Bala基础 |
| **Hora (时辰)** | ⚠️ | 部分 | 24小时分法 |
| **Chogadiya** | ❌ | — | 未实现 |
| **Abhijit Muhurta** | ❌ | — | 未实现 |
| **Pancha Pakshi** | ❌ | — | **6大缺失模块之一** |
| **Tarabala + Chandrabala** | ⚠️ | 部分 | 未完整 |
| **Rahu Kala** | ❌ | — | 未实现 |
| **Yama Ghanta** | ❌ | — | 未实现 |
| **Gulika Kala** | ❌ | — | 未实现 |
| **Vara (星期)** | ✅ | 基础 | 已内置 |
| **Karana** | ⚠️ | 部分 | 未完整 |

**覆盖度: 2/15 = 13%**

---

## 六、问事系统 (Prashna/Horary)

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Prashna Chart计算** | ✅ | prashna.py | 提问时刻星盘 |
| **Arudha for Prashna** | ✅ | prashna.py | 镜像点 |
| **Sphutas计算** | ✅ | prashna.py | 生命点 |
| **Sahams计算** | ✅ | prashna.py | 阿拉伯点 |
| **Lost Item Analysis** | ✅ | prashna.py | 寻物 |
| **Kunda Verification** | ✅ | prashna.py | Kunda盘验证 |
| **Prashna Significators** | ⚠️ | 部分 | 未完整 |
| **Tara Bala for Prashna** | ⚠️ | 部分 | 未完整 |
| **Chandrabala for Prashna** | ❌ | — | 未实现 |
| **Prashna Yoga Analysis** | ⚠️ | 部分 | 未完整 |

**覆盖度: 6/10 = 60%**

---

## 七、合盘系统 (Synastry)

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Ashta Kuta (8分体系)** | ✅ | synastry.py | Varna/Vashya/Tara/Yoni/Graha/Gana/Bhakuta/Nadi |
| **Mangal Dosha检测** | ✅ | synastry.py | 火星凶星位置 |
| **Papasamya (凶星平衡)** | ✅ | synastry.py | 比较双方凶星 |
| **Dasha Compatibility** | ✅ | synastry.py | 大运同步性 |
| **Nakshatra Compatibility** | ✅ | nakshatra_advanced.py | 28分 |
| **Composite Chart** | ❌ | — | 未实现 |
| **Davidson Chart** | ❌ | — | 未实现 |
| **Navamsa Overlay** | ⚠️ | 部分 | 未系统化 |
| **Kuta Score Interpretation** | ⚠️ | 有计算 | 解读模板化 |
| **Relationship Timing** | ❌ | — | 未实现 |

**覆盖度: 6/10 = 60%**

---

## 八、Tajika系统 (Annual Horoscopy)

| 技法 | 状态 | 所在模块 | 说明 |
|------|------|---------|------|
| **Varshaphala (年运盘)** | ✅ | tajika.py | 年度星盘 |
| **Muntha计算** | ✅ | tajika.py | 年度上升点 |
| **Year Lord计算** | ✅ | tajika.py | 年主星 |
| **Sahams (年度点)** | ⚠️ | tajika.py | 部分 |
| **Tajika Yogas** | ⚠️ | references/tajika-yoga-complete-guide.md | 16 Yogas，未完全实现 |
| **Mudda Dasha** | ✅ | tajika.py | 年度推运 |
| **Tri-Pataka** | ✅ | tajika.py | 年度凶象 |
| **Varsheshwara** | ⚠️ | 部分 | 未完整 |
| **Patyayini Dasha** | ❌ | — | 未实现 |

**覆盖度: 5/9 = 56%**

---

## 九、报告与解读系统

| 技法 | 状态 | 说明 |
|------|------|------|
| **结构化JSON输出** | ✅ | 所有模块 |
| **AI Reading Workflow** | ✅ | references/ai-reading-workflow-prompt.md |
| **Comprehensive Reading** | ✅ | references/comprehensive-reading-workflow.md |
| **Deep Analysis Workflow** | ✅ | references/deep-analysis-complete-workflow.md |
| **Report Builder** | ✅ | report_builder.py |
| **主题化报告** | ❌ | — | **需要从"模块罗列"升级为"主题叙事"** |
| **多维度交叉验证** | ❌ | — | D1/D9/RTN/Karaka综合判断 |
| **强度分级系统** | ⚠️ | references/yoga-strength-scoring-system.md | 未完全实现 |
| **时间锚定报告** | ⚠️ | 部分 | Dasha+Transit，未系统化 |
| **Actionable Output** | ✅ | references/transit-actionable-output-guide.md | 过境部分 |

**覆盖度: 6/10 = 60%**

---

## 十、综合覆盖度统计

### 按体系统计

| 体系 | 总技法数 | 已完成 | 部分完成 | 缺失 | 覆盖度 |
|------|---------|--------|---------|------|--------|
| 本命分析 | 95 | 35 | 28 | 32 | 37% |
| 推运系统 | 24 | 4 | 5 | 15 | 17% |
| 流年系统 | 16 | 6 | 4 | 6 | 38% |
| 择时系统 | 15 | 2 | 3 | 10 | 13% |
| 问事系统 | 10 | 6 | 2 | 2 | 60% |
| 合盘系统 | 10 | 6 | 1 | 3 | 60% |
| Tajika系统 | 9 | 5 | 2 | 2 | 56% |
| 报告解读 | 10 | 6 | 2 | 2 | 60% |
| **总计** | **189** | **70** | **47** | **72** | **37%** |

### 按层级统计

| 层级 | 总技法数 | 已完成 | 覆盖度 |
|------|---------|--------|--------|
| L1 基础计算 | 45 | 38 | 84% |
| L2 标准技法 | 78 | 28 | 36% |
| L3 高级技法 | 52 | 4 | 8% |
| L4 秘传技法 | 14 | 0 | 0% |

---

## 十一、六大缺失模块详情

### 模块1: Darakaraka深度解读 (DK Reader)
**状态**: ❌ 缺失
**重要性**: ⭐⭐⭐⭐⭐ (婚姻分析核心)
**来源文档**: references/darakaraka-complete-guide.md
**需要实现**:
- DK行星身份 → 配偶原型解读
- DK星座 → 特质表现方式
- DK宫位 → 关系生活领域
- DK Nakshatra → 精细能量
- DK相位 → 增强/挑战
- D9中DK → 灵魂层面伴侣
- DK逆行/燃烧 → 关系挑战
- 7星 vs 8星系统双轨分析

### 模块2: Rashi Tulya Navamsa (RTN)
**状态**: ❌ 缺失
**重要性**: ⭐⭐⭐⭐⭐ (隐藏力量分析)
**来源文档**: references/rashi-tulya-navamsa-root-impulse.md
**需要实现**:
- D9行星 → D1映射计算
- 12个分盘宫位名称生成
- 耀升/落陷取消检测
- Gunas平衡分析
- 凶星合相命名

### 模块3: 凶星合相命名 (Curse Yoga Detector)
**状态**: ❌ 缺失
**重要性**: ⭐⭐⭐⭐⭐ (健康/危机预警)
**来源文档**: 文章3 (Rashi Tulya Navamsa)
**需要实现**:
- Yama Yoga (火星+土星)
- Preta Yoga (土星+Rahu/Ketu)
- Rakshasa Yoga (火星+Rahu)
- Pisacha Yoga (火星+Ketu)
- 触发条件检测 (宫位 + Dasha)
- 强度分级
- 补救措施建议

### 模块4: 高地位配偶Yoga (Spouse Status)
**状态**: ❌ 缺失
**重要性**: ⭐⭐⭐⭐ (婚姻质量)
**来源文档**: references/high-status-spouse-yoga.md, 文章7
**需要实现**:
- 7宫 vs Lagna力量比较
- D9中7主星Rajyoga检测
- Upachaya宫分析 (从7宫起算)
- 婚后成长指数

### 模块5: Pancha Pakshi择时
**状态**: ❌ 缺失
**重要性**: ⭐⭐⭐ (择时核心)
**来源文档**: references/pancha-pakshi-nakshatra-systems.md
**需要实现**:
- 出生鸟计算 (Nakshatra + Paksha)
- 每日活动表生成
- 吉凶时段判断
- 活动相克规则

### 模块6: Tithi主星分析
**状态**: ❌ 缺失
**重要性**: ⭐⭐⭐ (情感模式)
**来源文档**: references/tithi-lord-relationship-system.md
**需要实现**:
- Tithi计算 (日月距离)
- Tithi主星查找
- 主星星座解读
- 主星宫位解读
- Tithi瑕疵检测

---

## 十二、优先级排序建议

### P0 (最高优先级) — 影响核心解盘质量

1. **Darakaraka深度解读** — ✅ v6.1.10 已接入 `full-reading.modules.jaimini.darakaraka`，并注入主题化婚姻报告；仍需外部传统案例 benchmark 深化。
2. **Rashi Tulya Navamsa** — ✅ v6.1.10 已从 `modules.rashi_tulya_navamsa` 注入婚姻/健康/灵性主题证据；当前仍为 partial，需继续完善变体与外部验证。
3. **主题化报告重构** — ✅ v6.1.8 已从"罗列"升级为消费 `full-reading.modules` 的真实叙事；v6.1.10 继续补入 DK/RTN 证据。
4. **Yoga F1提升至95%+** — ✅ v6.1.8 已达到 F1=95.22%，FP=36，FN=63。

### P1 (高优先级) — 丰富技法覆盖

5. **凶星合相命名** — 健康/危机预警
6. **高地位配偶Yoga** — 婚姻质量评估
7. **Tajika 16 Yogas完整实现** — 年运深度
8. **Jaimini Chara Dasha完善** — 推运体系补充

### P2 (中优先级) — 扩展高级技法

9. **Pancha Pakshi择时** — 择时系统核心
10. **Tithi主星分析** — 情感模式解读
11. **Ashtottari/Yogini Dasha** — 推运体系扩展
12. **Sahams系统完善** — 阿拉伯点

### P3 (低优先级) — 秘传/特殊技法

13. **Kalachakra Dasha** — 高级推运
14. **Narayana Dasha** — 需Drik Bala完备
15. **Moola Dasha** — 需D60完备
16. **D144 Nadiamsa** — 最精微分盘

---

## 十三、结论

### 当前引擎真实水平

| 维度 | 评分 | 说明 |
|------|------|------|
| **计算精度** | A- | 星盘/Dasha/Varga计算精确 |
| **技法覆盖度** | C+ | 约37%，大量高级技法缺失 |
| **解读深度** | C | 有计算但缺深度叙事 |
| **验证体系** | B+ | 60张标准盘，Yoga F1=95.22%（v6.1.8），并新增公开/虚构 benchmark 套件 |
| **文档完整度** | B+ | 105篇参考文档 |
| **工程化程度** | B | 模块化良好，但无统一API |

### 成为全球最好需要补什么

**短期 (达到"专业级")**:
- 继续补齐/验证6大缺失模块中尚未成熟的部分（DK/RTN/主题报告/Yoga 95%+ 已进入可用层）
- 维持 Yoga F1 ≥95%，避免为召回牺牲准确率
- 深化主题化报告的传统案例 benchmark 与 evidence ranking

**中期 (达到"专家级")**:
- 推运体系扩展 (Ashtottari/Yogini/Chara)
- 择时系统完善
- Tajika 16 Yogas完整

**长期 (达到"大师级")**:
- 所有分盘映射技法
- 所有Dasha系统
- 完整的力量评估体系
- 多维度交叉验证引擎
- 从"检测器"到"解读者"的质变

---

*此文档为活文档，随引擎发展持续更新。*
