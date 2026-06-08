# 开源吠陀占星（Jyotish）项目竞品分析报告

> 数据采集日期：2026-06-06 | 数据来源：GitHub API / PyPI / 项目官网

---

## 一、项目总览对比表

| 项目 | 仓库 | 语言 | Stars | Forks | 贡献者 | 最后提交 | 许可证 |
|------|------|------|-------|-------|--------|---------|--------|
| **PyJHora** | naturalstupid/PyJHora | Python | **184** | 102 | 1 | 2026-05-28 | AGPL-3.0 |
| **jyotisha** | jyotisham/jyotisha | TeX/Python | **127** | 62 | 4 | 2026-06-04 | MIT |
| **VedAstro** | VedAstro/VedAstro | C# | **561** | 248 | 11 | 2026-04-23 | MIT |
| **drik-panchanga** (原版) | webresh/drik-panchanga | Python | **139** | 112 | 1 | 2023-05-02 | AGPL-3.0 |
| **drik-panchanga** (bdsatish fork) | bdsatish/drik-panchanga | Python | **10** | 4 | 1 | 2026-03-18 | AGPL-3.0 |
| **Kerykeion** (西方占星为主) | g-battaglia/kerykeion | Python | **647** | 186 | 18 | 2026-06-05 | AGPL-3.0 |
| **VedicAstro** (KP系统) | diliprk/VedicAstro | Python/Jupyter | **62** | 31 | 1 | 2026-01-07 | MIT |
| **jyotishganit** | northtara/jyotishganit | Python | **31** | 13 | 2 | 2026-06-02 | MIT |

> **注意**：Kerykeion 主要是西方占星（Western Astrology）库，有 Sidereal 模式可选，列入作为参考对比。

---

## 二、各项目详细分析

### 1. PyJHora (naturalstupid/PyJHora) ⭐ 184

**定位**：最全面的吠陀占星 Python 计算库，复刻 Jagannatha Hora V8.0 全部功能

| 维度 | 详情 |
|------|------|
| **GitHub Stars** | 184 |
| **贡献者** | 1（Sundar Sundaresan，单人主力开发） |
| **最后版本** | v4.8.6 (2026-05-28) |
| **PyPI 下载** | PIP 可安装，活跃发布 |
| **测试覆盖** | ✅ **约 6800~7678 个测试用例**，所有计算与 JHora V8.0 逐项比对验证 |
| **验证基准** | ✅ **关键优势**：所有结果与 PVR Narasimha Rao 的著作例题和 JHora 软件逐一对比验证 |
| **完整分析管线** | ✅ 覆盖 47 种 Dasha 系统、300+ 分盘（D1-D300）、284+ 种 Yoga、22 种 Graha Dasha、多种匹配算法、Ashtakavarga、Tajaka 年运、生时校正 |
| **CI/质量门控** | ❌ 无 GitHub Actions CI 配置 |
| **文档** | ⚠️ 详细但不规范：README 含完整 changelog 式功能清单，但缺少标准 API 文档；API 文档散布在各模块 README |
| **GUI** | ✅ 基于 PyQt6 的完整图形界面 |
| **依赖** | pyswisseph (必需), PyQt6 (可选) |
| **核心优势** | JHora 般的全面性、6800+ 测试用例验证、持续活跃更新 |
| **核心劣势** | 单人维护、无 CI、文档非标准化 |

**关键结论**：功能最全的 Vedic Astrology Python 库，测试验证体系最完善，但文档质量和工程化程度有待提高。

---

### 2. jyotisha (jyotisham/jyotisha) ⭐ 127

**定位**：学术派的 Python 吠陀天文/历法计算工具

| 维度 | 详情 |
|------|------|
| **GitHub Stars** | 127 |
| **贡献者** | 4 |
| **最后提交** | 2026-06-04（活跃维护中） |
| **测试覆盖** | ✅ 有 `jyotisha_tests/` 目录，含 6 个测试文件 |
| **验证基准** | ❌ 未明确提及与任何权威软件/书籍的基准验证 |
| **完整分析管线** | ❌ 主要聚焦 Panchanga 计算和历法生成，**不是完整的星盘解读管线** |
| **CI/质量门控** | ✅ 3 个 GitHub Actions workflows + ReadTheDocs 自动构建 |
| **文档** | ✅ 完善的文档体系：ReadTheDocs API 文档 + GitHub Pages 用户指南 + 示例日历 |
| **主要功能** | Panchanga 五要素、日历生成、节日数据库（adyatithi 事件数据库） |
| **依赖** | 轻量级 Python 包 |
| **核心优势** | 学术背景、完善的 CI/CD 和文档体系、活跃社区 |
| **核心劣势** | **只做历法/天文计算，不做占星解读**；没有 Dasha/Yoga/Dosha 等占星分析功能 |

**关键结论**：最"学术规范"的项目，CI/文档体系最完善，但**定位是天文历法工具而非占星解读引擎**。

---

### 3. VedAstro (VedAstro/VedAstro) ⭐ 561

**定位**：全栈吠陀占星平台（C# 核心 + Python/Web 客户端）

| 维度 | 详情 |
|------|------|
| **GitHub Stars** | **561**（该项目中最高的） |
| **贡献者** | 11 |
| **最后提交** | 2026-04-23 |
| **测试覆盖** | ⚠️ 未明确披露测试数量或覆盖率 |
| **验证基准** | ❌ 未明确提及与权威来源的验证对比 |
| **完整分析管线** | ✅ 全栈方案：Web 界面 + Python API + AI 占星师 + 云引擎 |
| **CI/质量门控** | ✅ 1 个 GitHub Actions workflow |
| **文档** | ✅ 完善的官网文档（vedastro.org）+ Python 库文档 + 示例代码 |
| **API 能力** | **596+ 种占星计算**、47 种 Ayanamsa 系统、D1-D60 分盘、AI 生时填充、自然语言搜索 |
| **技术栈** | C# 核心引擎 + Python 轻量客户端（云端计算，本地零依赖） |
| **核心优势** | Star 数最高、社区最大、全栈方案、AI 驱动、零本地依赖 |
| **核心劣势** | **依赖云端 API**（有速率限制）、非纯离线方案、Python 客户端只是封装层 |

**关键结论**：Star 数最高、生态系统最完整，但 Python 库是云端 API 封装（非纯本地计算），且 C# 核心引擎可能对 Python 开发者不友好。

---

### 4. drik-panchanga (webresh/drik-panchanga) ⭐ 139

**定位**：轻量级观测式印度阴阳历计算器

| 维度 | 详情 |
|------|------|
| **GitHub Stars** | 139（原版） |
| **贡献者** | 1（作者已归档项目） |
| **最后提交** | 2023-05-02（**已停止维护**） |
| **测试覆盖** | ❌ 无独立测试文件 |
| **验证基准** | ⚠️ 依赖 Swiss Ephemeris 精度，提供手动验证示例（Madhvacharya 忌日） |
| **完整分析管线** | ❌ **只做 Panchanga 五要素计算**，无 Dasha/Yoga/Dosha/星盘解读 |
| **CI/质量门控** | ❌ 无 GitHub Actions |
| **文档** | ⚠️ 仅有 README，一份 Python 文件实现全部功能，缺乏 API 文档 |
| **功能范围** | Tithi/Nakshatra/Yoga/Karana/Vaara + 日出日落 + CLI 版支持 Navamsa/Dasha（有限） |
| **依赖** | pyswisseph + wxPython（GUI） |
| **核心优势** | 代码极简（单文件 ~1200 行）、纯计算无依赖、支持 Python 2/3 |
| **核心劣势** | **已停止维护**、无占星分析管线、功能范围窄 |

> **注**：bdsatish/drik-panchanga (10 stars) 是上个月才创建的新 fork，有更新活动但尚不成熟。

**关键结论**：优秀的轻量 Panchanga 计算器，但**已归档停更**，且只覆盖历法层，无任何占星分析。

---

### 5. Kerykeion (g-battaglia/kerykeion) ⭐ 647

**定位**：数据驱动的通用占星库（**非专属吠陀占星**）

| 维度 | 详情 |
|------|------|
| **GitHub Stars** | **647**（所有占星库中最高） |
| **贡献者** | **18**（社区最大） |
| **最后提交** | 2026-06-05（高度活跃） |
| **PyPI 月下载** | **140,000+** |
| **测试覆盖** | ⚠️ 有开发依赖 (`.[dev]`)，但未披露具体测试数量 |
| **验证基准** | ❌ 未提及任何吠陀占星验证基准 |
| **完整分析管线** | ✅ 本命盘/合盘/行运/回归盘 + SVG 图表 + 文本报告 + AI Context 序列化 |
| **CI/质量门控** | ❌ 无 GitHub Actions CI 配置（从 API 确认） |
| **文档** | ✅ **极完善**：kerykeion.net 官网 + API 文档 + 示例库 + 迁移指南 |
| **吠陀支持** | 支持 Sidereal 模式（48 种 Ayanamsa），但**不是吠陀专属库** |
| **核心优势** | 最大社区、最完善文档、SVG 图表生成、AI 报告、140K+ 月下载 |
| **核心劣势** | **主要面向西方占星**，吠陀特有功能（Dasha/Dosha/Yoga/分盘等）缺失或需自行实现 |

**关键结论**：社区最大、文档最好的占星库，但**不是吠陀占星专用**。可作为 UI/图表生成层参考，但无法替代 PyJHora 或 VedAstro 的吠陀计算能力。

---

### 6. VedicAstro (diliprk/VedicAstro) ⭐ 62

**定位**：专注 KP (Krishnamurti Paddhati) 系统的吠陀占星 Python 包

| 维度 | 详情 |
|------|------|
| **GitHub Stars** | 62 |
| **贡献者** | 1 |
| **最后提交** | 2026-01-07 |
| **测试覆盖** | ❌ 未提及测试 |
| **验证基准** | ❌ 未提及验证基准 |
| **完整分析管线** | ⚠️ 有限：生成星盘、行星数据、级征象星（ABCD）、Vimshottari Dasa |
| **CI/质量门控** | ❌ 无 GitHub Actions |
| **文档** | ⚠️ 仅有 README + PyPI 描述 |
| **主要功能** | KP 级征象星系统、KP 卜卦星盘、Vimshottari Dasa |
| **依赖** | pyswisseph + flatlib（需手动安装） |
| **核心优势** | KP 系统专注度高 |
| **核心劣势** | 依赖需要手动安装、文档不够完善、功能覆盖面窄 |

---

### 7. jyotishganit (northtara/jyotishganit) ⭐ 31

**定位**：新生代高精度吠陀占星 Python 库（NASA JPL 星历）

| 维度 | 详情 |
|------|------|
| **GitHub Stars** | 31 |
| **贡献者** | 2 |
| **最后版本** | v0.1.3 (2026-05-30) - **Beta 阶段** |
| **测试覆盖** | ❌ Beta 阶段，未披露测试 |
| **验证基准** | ❌ 未提及 |
| **完整分析管线** | ❌ 初期阶段，基础计算为主 |
| **CI/质量门控** | ✅ 2 个 GitHub Actions workflows |
| **文档** | ⚠️ 仅有 PyPI 描述和 GitHub README |
| **主要功能** | 高精度天文计算、NASA JPL 星历 |
| **核心优势** | NASA JPL 星历（非 Swiss Ephemeris）、现代化工程实践 |
| **核心劣势** | 极早期、功能有限、用户基数小 |

---

## 三、关键维度对比矩阵

| 维度 | PyJHora | jyotisha | VedAstro | drik-panchanga | Kerykeion |
|------|---------|----------|----------|----------------|-----------|
| Star 数 | 184 | 127 | **561** | 139 | **647** |
| 活跃维护 | ✅ 2026-05 | ✅ 2026-06 | ✅ 2026-04 | ❌ 已归档 | ✅ 2026-06 |
| 贡献者数 | 1 | 4 | 11 | 1 | 18 |
| **测试覆盖** | **6800+** 测试 | 有测试目录 | 未披露 | 无 | 有 dev 依赖 |
| **验证基准** | ✅ JHora 对比 | ❌ | ❌ | 手动示例 | ❌ |
| **完整管线** | ✅ 极全面 | ❌ 仅历法 | ✅ 全栈 | ❌ 仅历法 | ⚠️ 西占为主 |
| CI/CD | ❌ | ✅ 3 workflows | ✅ 1 workflow | ❌ | ❌ |
| 文档质量 | ⚠️ 详细但非标 | ✅ 标准化 | ✅ 官网完善 | ⚠️ 仅 README | ✅ 极完善 |
| 吠陀专用 | ✅ 是 | ✅ 是 | ✅ 是 | ✅ 是 | ❌ 偏西占 |
| 离线可用 | ✅ 完全离线 | ✅ 完全离线 | ❌ 依赖云API | ✅ 完全离线 | ✅ 完全离线 |
| GUI | ✅ PyQt6 | ❌ | ✅ Web UI | ✅ wxPython | ✅ SVG 图表 |
| 多语言 | ✅ 6种 | ❌ | ❌ | ✅ 梵文名 | ✅ 10种 |

---

## 四、竞争定位分析

### 按场景推荐

| 使用场景 | 推荐项目 | 理由 |
|----------|----------|------|
| **最全面的吠陀占星计算** | **PyJHora** | 6800+ 测试、与 JHora 逐项验证、覆盖最广功能 |
| **学术研究/历法计算** | **jyotisha** | 最佳工程实践、CI/CD、ReadTheDocs 文档 |
| **全栈 Web 应用/快速原型** | **VedAstro** | 最多 Star、云 API 零依赖、AI 集成 |
| **轻量 Panchanga 计算** | **drik-panchanga** | 单文件实现（但已停维） |
| **UI/图表可视化** | **Kerykeion** | 最佳 SVG 图表能力、最大社区（但非吠陀专用） |
| **KP (Krishnamurti) 系统** | **VedicAstro** | 唯一专注 KP 的库 |
| **极简/起步阶段** | **jyotishganit** | NASA JPL 星历（但 Beta 阶段） |

### PyJHora 的差异化优势

1. **验证体系**：唯一与 Jagannatha Hora V8.0 逐项验证的项目（6800+ 测试）
2. **功能广度**：47 种 Dasha 系统、300+ 分盘、284+ Yoga、22 种 Graha Dasha
3. **离线运行**：纯本地计算，无云端依赖
4. **活跃度**：v4.8.6 最新，持续月更
5. **GUI 支持**：PyQt6 多语言图形界面

### PyJHora 的主要差距

1. **工程化不足**：无 CI/CD、无标准化文档（API doc）、单人维护
2. **社区规模小**：184 stars vs VedAstro 561 和 Kerykeion 647
3. **文档体验差**：以 changelog 风格代替 API 参考文档
4. **没有 Web 端**：VedAstro 有完整 Web/AI 方案

---

## 五、社区声音摘要

搜索了 "best open source vedic astrology library"、"PyJHora vs drik-panchanga" 等关键词，社区讨论中的关键观点：

1. **PyJHora vs drik-panchanga 定位不同**：PyJHora 是综合占星库，drik-panchanga 只是日历计算器，二者不直接竞争
2. **VedAstro 最受欢迎**：Star 数最高，社区活跃，但 Python 封装依赖云端
3. **没有完美的项目**：PyJHora 功能最全但文档和工程化弱，VedAstro 社区最强但非纯 Python 离线，jyotisha 工程最佳但功能受限
4. **测试是 PyJHora 的核心壁垒**：6800+ 测试与 JHora 的对比验证是其他项目无法短期复制的

---

## 六、总结建议

| 竞争维度 | PyJHora 地位 | 建议改进方向 |
|----------|-------------|-------------|
| 功能完整性 | **行业标杆** | - |
| 验证准确性 | **唯一有系统验证** | - |
| 社区规模 | 中等 | 加大宣传、增加贡献者 |
| 工程化/CI | 弱 | **优先引入 GitHub Actions CI** |
| 文档质量 | 弱 | **重构文档结构，增加 API 参考** |
| 生态扩展 | 无 Web/API | 考虑提供轻量 API 层 |
| 活跃维护 | 好 | 持续保持 |
