# Jyotish Skill 功能差距矩阵 (2026)

> **版本基准**：Our Skill v6.1.10 vs 4个顶级对标项目
> **生成日期**：2026-06-10
> **对标项目**：
> - **JH** = Jagannatha Hora / PyJHora (AGPL) — 最权威免费Jyotish软件
> - **Kala** = Kala 2023 (商业) — 最全面的古典Jyotish软件
> - **JG** = jyotishganit v0.1.3 (MIT) — Python库
> - **PL** = Parashara's Light 9.0 (商业) — 专业级Jyotish软件

---

## 状态标记说明

| 标记 | 含义 |
|------|------|
| ✅已实现 | 我们有完整的知识+计算+工作流+输出 |
| ⚠️部分 | 有一些层但不完整，或精度未校准 |
| 📖仅知识 | 有参考文档但无可执行计算 |
| ❌缺失 | 无有意义的本地覆盖 |
| 🆕新增 | v6.0+新增的能力 |

## 可复用性标记

| 标记 | 含义 |
|------|------|
| ✅可直接复制 | MIT/AGPL许可，API兼容，代码可直接取用 |
| ⚠️需改编 | 有参考代码但需要重构才能适配我们的架构 |
| ❌仅借鉴 | 商业软件或闭源，只能参考功能列表不能取代码 |
| 🔧自行实现 | 无可用外部代码，需从零开发 |

---

## 一、基础排盘（Rasi, Navamsa, 全部Varga）

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| 基础排盘 | D1 Rasi Chart | ✅已实现 | 23+标准分盘+自定义 | 16分盘 | 14分盘 | 16+分盘 | JH/PyJHora | ✅可直接复制 |
| 基础排盘 | D2 Hora | ✅已实现 | 6种变体 | ✅ | ✅ | ✅ | JH (6变体) | ⚠️需改编 |
| 基础排盘 | D3 Drekkana | ✅已实现 | 4种变体 | ✅ | ✅ | ✅ | JH (4变体) | ⚠️需改编 |
| 基础排盘 | D4 Chaturthamsa | ✅已实现 | 2种变体 | ✅ | ✅ | ✅ | JH | ⚠️需改编 |
| 基础排盘 | D5 Panchamsa | ✅已实现(divisional_charts_extended) | 2种变体 | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| 基础排盘 | D6 Shashthamsa | ✅已实现(divisional_charts_extended) | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D7 Saptamsa | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D8 Ashtamsa | ✅已实现(divisional_charts_extended) | 2种变体 | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| 基础排盘 | D9 Navamsa | ✅已实现 | 3种变体 | ✅ | ✅ | ✅ | JH (3变体) | ⚠️需改编 |
| 基础排盘 | D10 Dasamsa | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D11 Ekadasamsa/Rudramsa | ✅已实现(divisional_charts_extended) | 2种变体 | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| 基础排盘 | D12 Dwadashamsa | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D16 Shodasamsa | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D20 Vimsamsa | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D24 Chaturvimsamsa | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D27 Bhamsa | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D30 Trimsamsa | ✅已实现 | 3种变体 | ✅ | ✅ | ✅ | JH (3变体) | ⚠️需改编 |
| 基础排盘 | D40 Khavedamsa | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D45 Akshavedamsa | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 基础排盘 | D60 Shashtiamsa | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| 高级分盘 | D81 Navamsamsa | ❌缺失 | ✅(2变体) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级分盘 | D108 | ❌缺失 | ✅(2变体) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级分盘 | D144 | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级分盘 | 自定义D-N (N≤300) | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级分盘 | 复合分盘 D-m×n | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级分盘 | Parivritta Dasamsa | ❌缺失 | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |
| 高级分盘 | Nadyamsa (Chandra Kala Nadi) | ❌缺失 | ✅(2法) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 分盘变体 | 各分盘的多种计算方法 | ❌缺失 | ✅(Hora 6变体, D3 4变体等) | ❌ | ❌ | ❌ | JH/PyJHora | ⚠️需改编 |

**差距总结**：我们实现了BPHS十六分盘(D2-D60)，但JH还支持D81/D108/D144/自定义D-N/复合分盘/多种变体算法。差距在于**分盘变体算法**和**高级分盘**。

---

## 二、Dasha系统

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| 星宿Dasha | Vimshottari Dasha | ✅已实现 | ✅(12种起算点) | ✅ | ✅ | ✅(10变体) | JH/PyJHora | ✅可直接复制 |
| 星宿Dasha | Vimshottari多起算点 | ⚠️部分(仅月亮/上升) | ✅(12种起算点) | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 星宿Dasha | Ashtottari Dasha | ✅已实现(ashtottari_dasha.py) | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 星宿Dasha | Yogini Dasha | ✅已实现(yogini_dasha.py) | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 星宿Dasha | Kalachakra Dasha | ✅已实现(kalachakra_dasha.py) | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 星宿Dasha | Dwisaptati Sama Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 星宿Dasha | Shattrimsa Sama Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 星宿Dasha | Dwadashottari Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 星宿Dasha | Chaturaseeti Sama Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 星宿Dasha | Satabdika Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 星宿Dasha | Shodasottari Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 星宿Dasha | Panchottari Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 星宿Dasha | Shashtihayani Dasha | 📖仅知识 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 星宿Dasha | Tribhagi变体 | ❌缺失 | ✅(适用于多数星宿Dasha) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Chara Dasha | ⚠️部分(24.17%匹配KN Rao) | ✅(Parasara+KN Rao) | ✅(KN Rao法) | ❌ | ✅ | JH | ⚠️需改编 |
| 宫位Dasha | Narayana Dasha | ✅已实现(narayana_dasha.py) | ✅(所有分盘) | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| 宫位Dasha | Lagnaamsaka Dasha | ❌缺失 | ✅(所有分盘) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Padanaathaamsa Dasha | ❌缺失 | ✅(所有分盘) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Sudasa | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Drigdasa | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Lagna Kendradi Rasi Dasha | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| 宫位Dasha | Atmakaraka Kendradi Rasi Dasha | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Trikona Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Yogardha Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Paryaaya Dasas (Sthira/Chara/Ubhaya) | ❌缺失 | ✅(适用于所有Varga) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Shoola Dasas | ❌缺失 | ✅(全12宫) | ❌ | ❌ | ✅ | JH | ⚠️需改编 |
| 宫位Dasha | Niryaana Shoola Dasha | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Brahma Dasha | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Sthira Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Manduka Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Navamsa Dasha | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 宫位Dasha | Varnada Dasha | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 其他Dasha | Moola Dasha (Pinda/Amsa/Naisarga) | ❌缺失 | ✅ | ✅(3种) | ❌ | ❌ | JH | ⚠️需改编 |
| 其他Dasha | Tara Dasha | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 其他Dasha | Patyayini Dasha | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 其他Dasha | Sudarsana Chakra Dasa | ✅已实现(sudarshana_chakra.py) | ✅ | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| 其他Dasha | Rasi-Bhukta Vimsottari | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 其他Dasha | Tithi Ashtottari/Yogini | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 其他Dasha | Bhrigu Pada Dasha | ✅已实现(bhrigu_pada_dasha.py) | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| Dasha深度 | 层级深度 | ⚠️部分(MD→AD→PD 3层) | ✅(最多7层) | ✅(Antardasa+) | ✅(MD+AD) | ✅(最多5层) | JH | ✅可直接复制 |
| Dasha深度 | Dasha Pravesha Chart | ❌缺失 | ✅(任意层级起始可绘制完整图) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Dasha深度 | 条件性Dasha筛选 | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| Dasha深度 | 年单位选项(5种) | ❌缺失 | ✅(回归年/吠陀年/自定义/太阳年/Tithi年) | ❌ | ❌ | ❌ | JH | ✅可直接复制 |

**差距总结**：JH有**30+种Dasha系统**，我们实现了约7种(Vimshottari/Ashtottari/Yogini/Kalachakra/Narayana/BhriguPada/Sudarshana)。Chara Dasha仅partial。缺少绝大多数宫位Dasha和星宿Dasha变体。**最大差距在宫位Dasha族**。

---

## 三、Ashtakavarga

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Ashtakavarga | Bhinna Ashtakavarga (BAV) | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH/PyJHora | ✅可直接复制 |
| Ashtakavarga | Sarvashtakavarga (SAV) | ✅已实现(SAV=337) | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Ashtakavarga | Prastara Ashtakavarga (PAV) | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ✅可直接复制 |
| Ashtakavarga | Sodhita Ashtakavarga | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ✅可直接复制 |
| Ashtakavarga | Sodhya Pindas | ❌缺失 | ✅(所有分盘) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Ashtakavarga | Graha Pinda | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Ashtakavarga | Rasi Pinda | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Ashtakavarga | Yoga Pinda | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Ashtakavarga | Trikona Reduction | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Ashtakavarga | Ekapatyapaksha Reduction | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Ashtakavarga | 分盘中计算AV | ❌缺失 | ✅(所有分盘) | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| Ashtakavarga | Kakshya评分 | ❌缺失 | ✅ | ❌ | ❌ | ✅ | JH | ✅可直接复制 |
| Ashtakavarga | 行运AV评分 | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Ashtakavarga | 吉祥方位 | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Ashtakavarga | 合盘中AV叠加 | ❌缺失 | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |

**差距总结**：我们有BAV+SAV基础计算，但缺少PAV展开表、Sodhita减法、Pinda体系、Kakshya评分、分盘级AV计算。JH和Kala在这些方面远超我们。

---

## 四、Tajika / Varshaphala

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Tajika | Varshaphala年运盘 | ✅已实现(tajika.py) | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Tajika | Muntha | ✅已实现(muntha.py) | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Tajika | Year Lord | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Tajika | Mudda Dasha | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Tajika | Tajika Yogas | 📖仅知识 | ✅(184种) | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| Tajika | Panchavargiya Bala | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH/Kala | ❌仅借鉴 |
| Tajika | Dvadashavargiya Bala | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH/Kala | ❌仅借鉴 |
| Tajika | Harsha Bala | ❌缺失 | ✅ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Tajika | Sahams (36种) | ❌缺失(仅Vivah Saham) | ✅(36种) | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Tajika | Saham时序 | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| Tajika | Hadda Dasha | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Tajika | Patyayini Dasha | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Tajika | 月运盘 Masa Phala | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Tajika | 日运盘 Dina Phala | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Tajika | Tajika Aspects | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| Tajika | Tithi Pravesha Chart | ❌缺失 | ✅ | ❌ | ❌ | ✅ | JH | ⚠️需改编 |
| Tajika | Yoga Pravesha Chart | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Tajika | Nakshatra Pravesha Chart | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |

**差距总结**：我们有基础年运盘+Muntha+YearLord+Mudda Dasha，但缺少Tajika力量体系(Panchavargiya/Harsha Bala)、完整Sahams、Tithi Pravesha等高级年运功能。

---

## 五、Shadbala

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Shadbala | Sthana Bala | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Shadbala | Kaala Bala | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Shadbala | Dig Bala | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Shadbala | Chesta Bala | ⚠️部分(速度分档近似) | ✅ | ✅(Parashara法) | ✅ | ✅ | JH/Kala | ⚠️需改编 |
| Shadbala | Naisargika Bala | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Shadbala | Drik Bala | ⚠️部分(简化相位权重) | ✅ | ✅ | ✅ | ✅ | JH | ⚠️需改编 |
| Shadbala | Ishta/Kashta Phala | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Shadbala | Bhava Bala | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Shadbala | Vimsopaka Bala | ✅已实现(vimsopaka_calculator.py) | ✅(4种分盘体系) | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| Shadbala | Vaiseshikamsa (Parijatamsa等) | ❌缺失 | ✅(4种分盘体系) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Shadbala | 行星战争(Shadbala内) | ⚠️部分 | ✅ | ✅(唯一Surya Siddhanta法) | ❌ | ❌ | Kala | ❌仅借鉴 |
| Shadbala | 外部绝对值校准 | ❌缺失 | ✅(参考标准) | ✅ | ✅ | ✅ | JH | 🔧自行实现 |

**差距总结**：我们六重力量框架完整但Chesta/Drik有简化项。最大缺口：Bhava Bala缺失、Vaiseshikamsa缺失、外部绝对值校准未完成。

---

## 六、Yoga识别

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Yoga | 基础Yoga引擎 | ✅已实现(yoga_engine.py, F1=95.22%) | ✅(184种) | ✅ | ❌ | ✅(1001+种) | JH | ✅可直接复制 |
| Yoga | Raja Yoga族 | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Yoga | Dhana Yoga族 | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Yoga | Neechabhanga Raja Yoga | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Yoga | Daridra Yoga | ✅已实现 | ✅ | ❌ | ❌ | ✅ | JH | ✅可直接复制 |
| Yoga | Curse Yoga | ✅已实现(curse_yoga_detector.py) | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| Yoga | 分盘中Yoga识别 | ❌缺失 | ✅(所有分盘) | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| Yoga | Tajika Yoga | 📖仅知识 | ✅(184种) | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| Yoga | Yoga搜索/筛选 | ❌缺失 | ✅ | ✅ | ❌ | ✅(研究模块) | JH | ⚠️需改编 |
| Yoga | Yoga强度评分 | ✅已实现(yoga-strength-scoring) | ❌ | ✅ | ❌ | ❌ | — | 🔧自行实现 |
| Yoga | 1001+ Yoga覆盖 | ❌缺失(~100条规则) | ✅(184) | ✅ | ❌ | ✅(1001+) | PL | ❌仅借鉴 |
| Yoga | Sankha Yoga误报修复 | ✅已实现 | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |

**差距总结**：我们Yoga精度高(F1=95.22%)但覆盖面窄(~100条 vs JH 184/PL 1001+)。关键缺口：分盘中Yoga识别、Tajika Yoga、更广泛的Yoga覆盖。

---

## 七、Transit / Gochar

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------| 
| Transit | 真实行星位置计算 | ✅已实现(Swiss Ephemeris) | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Transit | 多参考点Transit | ✅已实现(Lagna+Chandra Lagna) | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Transit | Double Transit (KN Rao) | ✅已实现(double-transit-pac) | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| Transit | Transit LL/7L连接 | ✅已实现(transit-ll7l) | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| Transit | 行星聚集检测 | ✅已实现(planetary-congregation) | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| Transit | AV行运评分 | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| Transit | Kakshya行运分析 | ❌缺失 | ✅ | ❌ | ❌ | ✅ | JH | ⚠️需改编 |
| Transit | Tara分类行运 | ❌缺失 | ✅(Karma等特殊Tara) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Transit | 行运日历(图形化) | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ❌仅借鉴 |
| Transit | 精确触发搜索 | ❌缺失 | ✅(精确到度分) | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| Transit | 动画行运 | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ❌仅借鉴 |
| Transit | 行星逆行/顺行追踪 | ⚠️部分 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Transit | 星座/Nakshatra切换时间 | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Transit | 食相预测 | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| Transit | Latta(踢击) | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Transit | Sade Sati追踪 | ❌缺失 | ❌ | ❌ | ❌ | ✅ | PL | ❌仅借鉴 |

**差距总结**：我们的Transit强在解读方法论(多参考点/Double Transit/LL7L)，但弱在可视化(日历/动画)和辅助计算(AV评分/Kakshya/精确搜索/食相)。

---

## 八、Synastry / Kuta匹配

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Synastry | Ashta Koota 36分 | ✅已实现(synastry.py) | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |
| Synastry | 月亮Gana/Kuta | ✅已实现 | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |
| Synastry | 所有行星+Lagna的Gana/Kuta | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Synastry | Rajju Dosha | ✅已实现(synastry.py additional_kutas) | ❌ | ✅ | ❌ | ❌ | dashaflow/Kala | ✅dashaflow MIT已适配 |
| Synastry | Vedha Dosha | ✅已实现(synastry.py additional_kutas) | ❌ | ✅ | ❌ | ❌ | dashaflow/Kala | ✅dashaflow MIT已适配 |
| Synastry | Strii-Diirgha | ✅已实现(synastry.py additional_kutas) | ❌ | ✅ | ❌ | ❌ | dashaflow/Kala | ✅dashaflow MIT已适配 |
| Synastry | Mahendra | ✅已实现(synastry.py additional_kutas) | ❌ | ✅ | ❌ | ❌ | dashaflow/Kala | ✅dashaflow MIT已适配 |
| Synastry | Vasya | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Synastry | Interaspects(交互相位) | ❌缺失 | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |
| Synastry | Davidson Chart | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Synastry | Composite Chart | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Synastry | AV叠加(合盘) | ❌缺失 | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |
| Synastry | 关系兼容性报告 | ❌缺失 | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |
| Synastry | Darakaraka深度解读 | ✅已实现(darakaraka_reader.py) | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| Synastry | 配偶六层确认法 | 📖仅知识 | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |

**差距总结**：我们已从基础Ashta Koota 36分扩展到 Mahendra / Stree Deergha / Vedha / Rajju / BadConstellations 附加Kuta，并保留 DK 解读；仍落后 Kala 的部分主要是所有行星+Lagna Kuta、Davidson/Composite、AV叠加与完整关系报告生成。JH没有合盘模块。

---

## 九、Muhurta

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Muhurta | Panchanga五要素 | ✅已实现(muhurta.py) | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Muhurta | Tarabala | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Muhurta | Chandrabala | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Muhurta | 吉凶温度计 | ❌缺失 | ❌ | ❌ | ❌ | ✅ | PL | ❌仅借鉴 |
| Muhurta | Rahu Kalam | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Muhurta | Gulika Kalam | ⚠️部分 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Muhurta | Yama Gandam | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Muhurta | Pancha Pakshi | ✅已实现(pancha_pakshi.py) | ❌ | ❌ | ❌ | ✅ | — | 🔧自行实现 |
| Muhurta | Suunya Rasis/Tithis | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Muhurta | Panchaka | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Muhurta | 时间调整工具 | ❌缺失 | ❌ | ❌ | ❌ | ✅ | PL | ❌仅借鉴 |
| Muhurta | 批量择时搜索 | ❌缺失 | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |

**差距总结**：我们有Panchanga+Tarabala+Chandrabala+Pancha Pakshi，但Kala有最完整的Muhurta模块(Suunya/Panchaka等)。PL有可视化择时工具。

---

## 十、Prashna

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Prashna | 基础Prashna星盘 | ✅已实现(prashna.py) | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Prashna | Arudha计算 | ✅已实现 | ✅ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| Prashna | Sphuta计算 | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| Prashna | Trisphuta | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH/Kala | ⚠️需改编 |
| Prashna | Chatursphuta | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Prashna | Prana/Deha/Mrityu | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| Prashna | 数字选Prashna(1-108) | ❌缺失 | ✅ | ❌ | ❌ | ✅ | JH | ✅可直接复制 |
| Prashna | KP数字选(1-249) | ❌缺失 | ✅ | ❌ | ❌ | ✅ | JH | ✅可直接复制 |
| Prashna | KP 16分盘数字选(1-1800) | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ✅可直接复制 |
| Prashna | Chandra Kriyas/Velas/Avasthas | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Prashna | Yama Sukra | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Prashna | Sahams(Prashna) | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ⚠️需改编 |

**差距总结**：我们有基础Prashna+Arudha，但缺少Sphuta/Trisphuta/Prana-Deha-Mrityu/数字选盘等关键Prashna工具。

---

## 十一、Jaimini

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Jaimini | Chara Karaka (7星制) | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Jaimini | Chara Karaka (8星制) | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Jaimini | Karakamsa / Swamsha | ✅已实现 | ✅ | ❌ | ❌ | ✅ | JH | ✅可直接复制 |
| Jaimini | Atmakaraka | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Jaimini | Arudha Pada (12宫) | ✅已实现(jaimini.py A1-A12/UL) | ✅(Rasi+分盘) | ✅ | ❌ | ✅ | dashaflow/jaimini-tropical/JH | ✅MIT思路已适配 |
| Jaimini | Chandra Arudha / Surya Arudha | ❌缺失 | ✅(12个) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Jaimini | Graha Arudha / Graha Pada | ✅已实现(jaimini.py Graha Pada) | ✅(9星+双Graha) | ❌ | ❌ | ❌ | jaimini-tropical/JH | ✅MIT思路已适配 |
| Jaimini | Chara Dasha | ⚠️部分(24.17%匹配) | ✅(2法) | ✅(KN Rao) | ❌ | ✅ | JH/jaimini-tropical | ⚠️需继续对标 |
| Jaimini | Jaimini力量体系 | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| Jaimini | 分盘中Arudha Pada | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| Jaimini | Upapada Lagna | ✅已实现 | ✅ | ❌ | ❌ | ❌ | — | 🔧自行实现 |

**差距总结**：Jaimini静态分析(AK/Karakamsa/A1-A12/UL/Graha Pada/Argala)覆盖明显增强；Chara Dasha timing 仍为 partial，仍缺 Chandra/Surya Arudha、分盘级 Arudha 与完整 KN Rao/PVN Rao/Iranganti Chara Dasha 回归。

---

## 十二、Panchang

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Panchang | Tithi | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Panchang | Nakshatra | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Panchang | Yoga | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Panchang | Karana | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Panchang | Vara | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Panchang | 日出/日落 | ✅已实现 | ✅(3种定义) | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Panchang | 月出/月落 | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Panchang | Hora (24个) | ⚠️部分 | ✅(24个Hora结束时间) | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Panchang | Vyatipata | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| Panchang | Vaidhriti | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| Panchang | 批量Panchanga(月度) | ❌缺失 | ✅ | ❌ | ❌ | ✅ | JH | ✅可直接复制 |
| Panchang | 太阴年/月 | ⚠️部分 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| Panchang | 特殊Tithi(Janma等) | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |

**差距总结**：Panchang五要素全覆盖，但缺日出/月出精度选项、Vyatipata/Vaidhriti、批量生成、特殊Tithi分类。

---

## 十三、Nakshatra

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Nakshatra | 基础Nakshatra定位 | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Nakshatra | Pada | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Nakshatra | Tara Bala | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Nakshatra | Chandra Bala | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Nakshatra | Sub-Lord (KP) | ✅已实现 | ✅(5级) | ✅(5级) | ❌ | ✅ | JH | ✅可直接复制 |
| Nakshatra | Navatara系统 | ✅已实现 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| Nakshatra | 特殊Tara(Karma等) | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Nakshatra | Nakshatra相位 | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Nakshatra | Latta(踢击) | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Nakshatra | Nakshatra Devata/神祇 | 📖仅知识 | ❌ | ❌ | ❌ | ✅ | — | 🔧自行实现 |

**差距总结**：基础Nakshatra+Tara+KP覆盖好，但缺特殊Tara/Nakshatra相位/Latta等高级功能。

---

## 十四、Remedies

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Remedies | 补救措施推荐 | 📖仅知识(references) | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| Remedies | 宝石推荐 | 📖仅知识 | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| Remedies | Mantra推荐 | 📖仅知识 | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |

**差距总结**：Remedies在所有4个对标项目中都不是计算模块，属于解读层面。我们有参考文档但无可执行输出。

---

## 十五、Bhava系统

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Bhava | 整宫制(Whole Sign) | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| Bhava | 等宫制(Equal 30°) | ✅已实现(bhava_chalit.py) | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Bhava | Bhava Chalit | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Bhava | Sripathi/Porphyry | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| Bhava | Placidus | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| Bhava | Koch | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ✅可直接复制 |
| Bhava | Regiomontanus | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ✅可直接复制 |
| Bhava | Campanus | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ✅可直接复制 |
| Bhava | 基于月亮/太阳起算 | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Bhava | Lagna起点/中点选项 | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Bhava | KP宫头制 | ❌缺失 | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |

**差距总结**：我们只有整宫制和等宫制+Bhava Chalit，JH支持12种宫位系统。这是一个显著差距，尤其对Sripathi用户。

---

## 十六、天体历（Ephemeris）

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| Ephemeris | Swiss Ephemeris行星位置 | ✅已实现 | ✅ | ✅ | ✅(JPL DE421) | ✅ | — | — |
| Ephemeris | 批量月度星历表 | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Ephemeris | 交互式星历表 | ❌缺失 | ❌ | ✅ | ❌ | ✅ | Kala | ❌仅借鉴 |
| Ephemeris | 图形星历表 | ❌缺失 | ❌ | ❌ | ❌ | ✅ | PL | ❌仅借鉴 |
| Ephemeris | 行星速度/距离/赤经/赤纬 | ⚠️部分 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| Ephemeris | 会合/冲搜索 | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| Ephemeris | 星座切换追踪 | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ✅可直接复制 |
| Ephemeris | 日期范围 | 5400BC-5400AD | 5400BC-5400AD | 5400BC-5400AD | ✅ | 5400BC-5400AD | — | — |

**差距总结**：天文精度对齐（Swiss Ephemeris），但缺批量星历表生成、行星天文数据完整输出、会合搜索。

---

## 十七、其他高级功能

| 功能域 | 具体技法 | 我们的状态 | JH | Kala | JG | PL | 最佳开源来源 | 代码可复用？ |
|--------|---------|-----------|-----|------|----|----|-------------|-------------|
| 高级 | Ayanamsa多选项 | ⚠️部分(Lahiri) | ✅(6+预设+自定义) | ✅ | ✅(Chitra Paksha) | ✅ | JH | ✅可直接复制 |
| 高级 | Upagrahas (Gulika/Mandi等) | ⚠️部分 | ✅(+9个Upagrahas) | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 高级 | Doomadi Upagrahas | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 高级 | 特殊Lagna (Bhava/Hora/Ghati等) | ✅已实现(special_lagnas.py) | ✅(11+) | ✅(7) | ❌ | ✅ | JH | ✅可直接复制 |
| 高级 | Varnada Lagna | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级 | Indu Lagna | ✅已实现 | ✅ | ❌ | ❌ | ❌ | JH | ✅可直接复制 |
| 高级 | Sahams (36种) | ⚠️部分(仅Vivah Saham) | ✅(36种) | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 高级 | Mrityu Bhaga (致命度数) | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 高级 | Pushkara Bhaga | ✅已实现 | ✅(2种定义) | ✅ | ❌ | ❌ | JH | ✅可直接复制 |
| 高级 | 64th Navamsa | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级 | 22nd Drekkana | ❌缺失 | ✅(4种定义) | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级 | Avastha (Baladi/Jagradadi) | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 高级 | Sayanadi Avastha | ❌缺失 | ✅(所有Varga) | ✅(所有Varga) | ❌ | ✅ | JH | ⚠️需改编 |
| 高级 | Sudarshana Chakra | ✅已实现 | ✅ | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| 高级 | Kalachakra | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级 | Kota Chakra | ❌缺失 | ✅ | ❌ | ❌ | ✅ | JH | ⚠️需改编 |
| 高级 | Sarvatobhadra Chakra | ❌缺失 | ✅ | ❌ | ❌ | ✅ | JH | ⚠️需改编 |
| 高级 | 行星关系(永久/临时/复合) | ✅已实现 | ✅ | ✅ | ✅ | ✅ | JH | ✅可直接复制 |
| 高级 | Pachakadi关系 | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级 | 推进(Progression) | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ⚠️需改编 |
| 高级 | 世俗占星(Mundane) | ❌缺失 | ✅ | ✅ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级 | 寿命计算(Ayurdaya) | ❌缺失 | ❌ | ✅(Pindaadi) | ❌ | ❌ | Kala | ❌仅借鉴 |
| 高级 | 出生时间矫正 | 📖仅知识 | ❌ | ❌ | ❌ | ✅(交互式) | PL | ❌仅借鉴 |
| 高级 | 研究模块(群体分析) | ❌缺失 | ❌ | ❌ | ❌ | ✅ | PL | ❌仅借鉴 |
| 高级 | 行星战争(精确计算) | ⚠️部分 | ✅ | ✅(唯一Surya Siddhanta法) | ❌ | ❌ | Kala | ❌仅借鉴 |
| 高级 | 燃烧(Combustion, 多法) | ⚠️部分 | ✅ | ✅(当代+Surya Siddhanta) | ❌ | ❌ | Kala | ❌仅借鉴 |
| 高级 | 外行星(天王/海王/冥王) | ❌缺失 | ✅ | ✅ | ❌ | ✅ | JH | ✅可直接复制 |
| 高级 | 小行星 | ❌缺失 | ❌ | ✅ | ❌ | ❌ | Kala | ❌仅借鉴 |
| 高级 | Kunda(出生时间矫正用) | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级 | Bhrigu Bindu | ❌缺失 | ✅ | ❌ | ❌ | ❌ | JH | ⚠️需改编 |
| 高级 | Yogi/Avayogi行星 | ✅已实现 | ✅ | ❌ | ❌ | ✅ | — | 🔧自行实现 |
| 高级 | Rashi Tulya Navamsa | ✅已实现 | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| 高级 | Argala | ✅已实现 | ✅ | ❌ | ❌ | ❌ | JH | ✅可直接复制 |
| 高级 | 五系统Dasha Convergence | ✅已实现 | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| 高级 | Full-reading自动化解盘 | ✅已实现(47模块) | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| 高级 | MEVG外部验证门控 | ✅已实现 | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |
| 高级 | 主题化报告桥接 | ✅已实现 | ❌ | ❌ | ❌ | ❌ | — | 🔧自行实现 |

---

## 十八、综合统计

### 我们的能力统计

| 状态 | 数量 | 百分比 |
|------|------|--------|
| ✅已实现 | 72 | 39.6% |
| ⚠️部分 | 18 | 9.9% |
| 📖仅知识 | 6 | 3.3% |
| ❌缺失 | 86 | 47.2% |
| **总计** | **182** | **100%** |

### 按功能域统计

| 功能域 | ✅已实现 | ⚠️部分 | ❌缺失 | 覆盖率 |
|--------|---------|--------|--------|--------|
| 基础排盘(Varga) | 19 | 0 | 7 | 73.1% |
| Dasha系统 | 7 | 2 | 27 | 23.1% |
| Ashtakavarga | 2 | 0 | 13 | 13.3% |
| Tajika/Varshaphala | 4 | 0 | 13 | 23.5% |
| Shadbala | 7 | 2 | 3 | 58.8% |
| Yoga识别 | 5 | 0 | 5 | 50.0% |
| Transit/Gochar | 4 | 1 | 10 | 26.7% |
| Synastry/Kuta | 2 | 0 | 11 | 15.4% |
| Muhurta | 4 | 1 | 6 | 36.4% |
| Prashna | 2 | 0 | 8 | 20.0% |
| Jaimini | 5 | 1 | 4 | 50.0% |
| Panchang | 5 | 1 | 6 | 41.7% |
| Nakshatra | 4 | 0 | 3 | 57.1% |
| Bhava系统 | 3 | 0 | 6 | 33.3% |
| 天体历 | 1 | 1 | 5 | 14.3% |
| 其他高级 | 8 | 4 | 21 | 22.7% |

### 与对标项目的整体对比

| 维度 | 我们 | JH | Kala | JG | PL |
|------|------|-----|------|----|----|
| 分盘种类 | 20种(BPHS十六分盘+D5/D6/D8/D11) | 23+标准+自定义D300 | 16+ | 14 | 16+ |
| Dasha系统 | 7种(1 partial) | 30+种 | 24+种 | 1种 | 23+种 |
| Ashtakavarga | BAV+SAV | BAV+SAV+PAV+Sodhita+Pindas | 完整Pinda体系 | BAV+SAV | BAV+SAV+Kakshya |
| 行星位置精度 | Swiss Ephemeris | Swiss Ephemeris | Swiss Ephemeris | JPL DE421 | Swiss Ephemeris |
| 宫位系统 | 2种 | 12种 | 4+种 | 1种 | 4+种 |
| Ayanamsa选项 | 1种(Lahiri) | 6+种+自定义 | 多种 | 1种 | 多种 |
| Yoga覆盖 | ~100条 | 184种 | 未知 | 0 | 1001+种 |
| KP系统 | Sub-Lord基础 | 5级Sub | 5级Sub | ❌ | 完整 |
| 交互式UI | CLI+AI对话 | GUI | GUI | 无UI | GUI |
| 解读深度 | AI驱动+方法论 | 纯计算 | 纯计算 | 纯计算 | 计算+文本 |
| 外部验证 | MEVG强制 | ❌ | ❌ | ❌ | ❌ |

---

## 十九、优先级建议

### P0 — 核心差距（影响专业可信度）

| 序号 | 差距 | 来源 | 可复用性 | 预估工作量 |
|------|------|------|---------|-----------|
| 1 | Chara Dasha完整实现(KN Rao法) | JH/PyJHora | ⚠️需改编 | 大 |
| 2 | 分盘级Ashtakavarga | JH | ⚠️需改编 | 中 |
| 3 | Bhava Bala计算 | JH | ✅可直接复制 | 小 |
| 4 | PAV/Sodhita Ashtakavarga | JH | ✅可直接复制 | 中 |
| 5 | 完整36 Sahams | JH | ✅可直接复制 | 中 |
| 6 | Ayanamsa多选项 | JH | ✅可直接复制 | 小 |

### P1 — 重要功能（对标专业软件）

| 序号 | 差距 | 来源 | 可复用性 | 预估工作量 |
|------|------|------|---------|-----------|
| 7 | 宫位Dasha族(Narayana扩展+Sthira+Trikona等) | JH | ⚠️需改编 | 大 |
| 8 | Vimshottari多起算点(12种) | JH | ✅可直接复制 | 中 |
| 9 | Sayanadi Avastha | JH | ⚠️需改编 | 中 |
| 10 | Sripathi宫位制 | JH | ✅可直接复制 | 小 |
| 11 | Trisphuta/Prana-Deha-Mrityu | JH | ✅可直接复制 | 中 |
| 12 | 批量星历表生成 | JH | ✅可直接复制 | 中 |
| 13 | 外行星支持 | JH | ✅可直接复制 | 小 |
| 14 | D81/D108高级分盘 | JH | ⚠️需改编 | 中 |

### P2 — 增强功能（差异化竞争力）

| 序号 | 差距 | 来源 | 可复用性 | 预估工作量 |
|------|------|------|---------|-----------|
| 15 | 合盘高级功能(Rajju/Vedha/Davidson) | Kala | ❌仅借鉴 | 大 |
| 16 | Chakra系统(Kalachakra/Kota/Sarvatobhadra) | JH | ⚠️需改编 | 中 |
| 17 | Tajika力量(Panchavargiya/Harsha Bala) | Kala | ❌仅借鉴 | 中 |
| 18 | 寿命计算(Pindaadi Ayurdaya) | Kala | ❌仅借鉴 | 大 |
| 19 | 世俗占星 | JH | ⚠️需改编 | 大 |
| 20 | Tithi Pravesha/Nakshatra Pravesha | JH | ⚠️需改编 | 中 |

---

## 二十、我们的独特优势（对标项目没有的）

| 序号 | 优势 | 对标项目状态 |
|------|------|-------------|
| 1 | Full-reading自动化47模块解盘 | 所有4个项目都没有 |
| 2 | MEVG外部验证门控 | 所有4个项目都没有 |
| 3 | 五系统Dasha Convergence | 所有4个项目都没有 |
| 4 | Double Transit PAC (KN Rao法) | 所有4个项目都没有 |
| 5 | AI驱动的深度解读+现代措辞 | 所有4个项目都没有 |
| 6 | 主题化报告桥接(婚姻/事业/健康/财富/灵性) | 所有4个项目都没有 |
| 7 | Yoga精度F1=95.22%(持续优化) | JH有Yoga但无精度指标 |
| 8 | Rashi Tulya Navamsa映射 | 所有4个项目都没有 |
| 9 | Darakaraka深度解读模块 | 所有4个项目都没有 |
| 10 | 行星聚集检测+Transit LL/7L | 所有4个项目都没有 |
| 11 | 15,807条AA级名人案例库 | JH有数据但不在软件内 |
| 12 | 技法注册中心(Technique Registry) | 所有4个项目都没有 |
| 13 | Strict Workflow Router(自动路由) | 所有4个项目都没有 |

---

> **结论**：我们的核心差距在**Dasha系统的广度**(7/30+种)和**Ashtakavarga的深度**(缺PAV/Sodhita/Pinda)。我们的独特优势在**AI驱动的自动化解盘+方法论+外部验证**，这是所有GUI计算软件不具备的。建议优先补齐P0差距，然后利用PyJHora(AGPL)的开源代码快速扩展Dasha和Ashtakavarga覆盖面。
