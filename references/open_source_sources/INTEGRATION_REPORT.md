# 开源印度占星项目整合报告

**日期**: 2026-06-11
**目标目录**: `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology/references/open_source_sources/`

---

## 项目1: CNWU16/vedic-astro-skills (MIT, 161 stars)

**仓库**: https://github.com/CNWU16/vedic-astro-skills
**本地路径**: `vedic-astro-skills/`
**许可证**: MIT License (Copyright 2026)

### 目录结构
```
vedic-astro-skills/
├── .github/
├── .gitignore
├── CHANGELOG.md
├── LICENSE                    # MIT License
├── README.md
├── sync_skills.ps1
├── antigravity/skills/        # Antigravity IDE 版本
│   ├── vedic-calculator/     # 核心计算引擎
│   │   ├── SKILL.md
│   │   ├── requirements.txt
│   │   └── scripts/
│   │       ├── engine.py              # ★ 主计算引擎 (688行)
│   │       ├── ashtakavarga_pyjhora.py
│   │       ├── dasha_pyjhora.py
│   │       ├── divisional_pyjhora.py
│   │       ├── shadbala_pyjhora.py
│   │       ├── transit.py
│   │       ├── extras_pyjhora.py
│   │       ├── formatter.py
│   │       ├── setup_env.py
│   │       └── ephe/                 # 星历文件
│   ├── vedic-core/           # 核心解读引擎
│   │   ├── SKILL.md          # ★ 3000+行，极详细的解读方法论
│   │   ├── scripts/report_builder.py
│   │   └── resources/
│   │       ├── house_framework.md    # ★ 宫位诊断框架
│   │       ├── p1_p12.md             # ★ P1-P12行星审计参数
│   │       ├── qa_rules.md           # Q&A伦理规则
│   │       ├── report_rules.md       # 报告打包规则
│   │       └── yogas.md              # ★ 格局(Yoga)评估方法论
│   ├── vedic-career/SKILL.md
│   ├── vedic-love/SKILL.md
│   ├── vedic-reader/         # 星盘阅读
│   │   ├── SKILL.md
│   │   └── resources/
│   │       ├── chart_reading_rules.md
│   │       ├── data_contract.md
│   │       └── validation_rules.md
│   └── vedic-rectifier/      # 出生时间校正
│       ├── SKILL.md
│       ├── requirements.txt
│       ├── scripts/time_scan.py
│       └── resources/event_house_map.md
├── claude-code/               # Claude Code 版本 (相同结构)
├── codex/                     # Codex 版本 (相同结构)
├── assets/                    # 赞赏二维码
└── scripts/report_builder.py
```

### Python 文件及 main 函数

| 文件路径 | 行数 | main函数 | 功能 |
|---------|------|---------|------|
| `antigravity/skills/vedic-calculator/scripts/engine.py` | 768 | `if __name__ == '__main__':` L694 | 主计算引擎 - 完整星盘计算 |
| `antigravity/skills/vedic-calculator/scripts/ashtakavarga_pyjhora.py` | - | - | SAV/BAV 计算 (PyJHora) |
| `antigravity/skills/vedic-calculator/scripts/dasha_pyjhora.py` | - | - | Vimshottari Dasha (PyJHora) |
| `antigravity/skills/vedic-calculator/scripts/divisional_pyjhora.py` | - | - | 分盘计算 D2-D60 (PyJHora) |
| `antigravity/skills/vedic-calculator/scripts/shadbala_pyjhora.py` | - | - | Shadbala 六重力量 + 9项bug修正 |
| `antigravity/skills/vedic-calculator/scripts/transit.py` | - | - | 行运计算 (自建, 非PyJHora) |
| `antigravity/skills/vedic-calculator/scripts/extras_pyjhora.py` | - | - | Bhava Bala, Special Lagnas 等 |
| `antigravity/skills/vedic-calculator/scripts/formatter.py` | - | - | 格式化输出 |
| `antigravity/skills/vedic-calculator/scripts/setup_env.py` | - | - | 环境安装脚本 |
| `antigravity/skills/vedic-core/scripts/report_builder.py` | - | - | HTML报告打包工具 |
| `antigravity/skills/vedic-rectifier/scripts/time_scan.py` | - | - | 出生时间扫描校正 |

### 核心技术特性

#### engine.py 核心功能 (calculate_full_chart)
- 基于 swisseph (pysweph) + dashaflow + PyJHora 混合架构
- 17个数据板块: ayanamsa, lagna, 9行星, SAV/BAV, D9/D10/D4/D5分盘, Vargottama, Dignity(Panchadha Maitri), Combustion, Chara Karakas, Aspects, House Lords, Dasha, Shadbala, Moon Phase, Digbala, Special Points(AL/UL), Transits(Sade Sati + Double Transit)
- fail-fast 策略: PyJHora 核心模块必须全部加载
- BPHS Panchadha Maitri 算法自建实现 (L576-596)
- Sade Sati 判定位于 calc_transits() L409-418
- 支持 Gandhi 测试用例

#### vedic-core SKILL.md 解读方法论
- **Step 1**: P1-P12 行星审计 (信号分诊 A/B/C 级 + PAC 联合判定)
- **Step 2**: 分盘交叉分析 (D9生命矩阵继承铁律 + D10/D4/D5)
- **Step 3**: 宫位诊断 (管理者/租客/相位/硬件四维度 + Dasha事件关联)
- **Step 4**: 十大板块总结 (人格/财富/事业/感情/健康/教育/家庭/社交/灵性/赛道)
- **Step 5**: 技术附录
- 盲审原则（Step 1-3纯盲审，禁止反推）
- 语言风格规则（70%通俗+20%数据+10%技术注释）
- Q&A模式（完成报告后答疑）

#### resource/yogas.md 格局列表
24种Yoga: Dharma-Karma, Dhana, Raja, Viparita Raja, Gajakesari, Chandra-Mangala, Kemadruma, Pancha Mahapurusha (Ruchaka/Bhadra/Hamsa/Malavya/Shasha)

### 与当前 yinduzhanxing Skill 对比

| 功能 | vedic-astro-skills | 当前 jyotish-vedic-astrology |
|------|-------------------|---------------------------|
| 计算引擎 | swisseph + PyJHora + dashaflow | swisseph + dashaflow |
| 核心解读 | 极详细 (3000行SKILL.md, KN Rao体系) | 分散在各模块 |
| P1-P12体系 | 完整定义 | 无 |
| 格局列表 | 24种Yoga + 评估框架 | 基本Yoga |
| 宫位诊断 | 管理者/租客/相位/硬件四维度 | 基础宫位分析 |
| 报告生成 | HTML打包工具 (report_builder.py) | 无 |
| 出生时间校正 | time_scan.py | 无 |
| 解读方法论 | 盲审原则/信号分诊/PAC联合判定 | 基础解读规则 |

---

## 项目2: diliprk/VedicAstro (MIT, 63 stars)

**仓库**: https://github.com/diliprk/VedicAstro
**本地路径**: `VedicAstro/`
**许可证**: MIT (需确认，仓库无LICENSE文件，但README标注MIT)

### 目录结构
```
VedicAstro/
├── vedicastro/
│   ├── __init__.py            # 空文件
│   ├── VedicAstro.py         # ★ 主类 VedicHoroscopeData (615行)
│   ├── horary_chart.py       # KP Horary 方法
│   ├── utils.py              # 工具函数
│   └── data/
│       └── KP_SL_Divisions.csv  # KP SubLord 度数表 (249条)
└── test_suite/
    ├── horary_functions_test.py
    └── swe_const.py
```

### Python 文件及 main函数

| 文件路径 | 行数 | main函数 | 功能 |
|---------|------|---------|------|
| `vedicastro/VedicAstro.py` | 615 | - | KP Sublord/Subsublord 计算引擎 |
| `vedicastro/horary_chart.py` | 149 | L131 | KP Horary 上升校正 |
| `vedicastro/utils.py` | 162 | - | UTC/DMS/日期工具 |
| `test_suite/horary_functions_test.py` | - | - | 测试 |

### KP Sublord/Subsublord 计算逻辑 ★★★

核心函数: `VedicHoroscopeData.get_rl_nl_sl_data()` (L241-288)

```python
def get_rl_nl_sl_data(self, deg: float):
    """
    返回: Rashi Lord, Nakshatra, Nakshatra Pada, Nakshatra Lord, 
          Sub Lord, Sub Sub Lord
    """
    duration = [7, 20, 6, 10, 7, 18, 16, 19, 17]  # Vimshottari年份
    lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    star_lords = lords * 3  # 27 Nakshatras
    
    # 1. 星座主 (Sign Lord): 每30度一个星座
    sign_index = int(sign_deg // 30)
    
    # 2. Nakshatra: 每13.332度一个星宿
    nakshatra_index = int(sign_deg // 13.332)
    pada = int((nakshatra_deg % 13.332) // 3.325) + 1
    
    # 3. KP SubLord/SubSubLord 算法 (KP经典三段嵌套)
    deg = deg - 120 * int(deg / 120)  # 归化到[0,120)
    degcum = 0
    i = 0
    while i < 9:
        deg_nl = 360 / 27           # Nakshatra跨度
        j = i
        while True:
            deg_sl = deg_nl * duration[j] / 120  # Sublord跨度
            k = j
            while True:
                deg_ss = deg_sl * duration[k] / 120  # SubSubLord跨度
                degcum += deg_ss
                if degcum >= deg:
                    return {
                        "Nakshatra": ..., "Pada": ...,
                        "NakshatraLord": ..., "RasiLord": ...,
                        "SubLord": lords[j],
                        "SubSubLord": lords[k]
                    }
                k = (k + 1) % 9
                if k == j: break
            j = (j + 1) % 9
            if j == i: break
        i += 1
```

**KP三段嵌套算法说明**:
1. 外层循环: 9个Nakshatra主星 (i=0..8)
2. 中层循环: 该Nakshatra下的9个SubLord (j从i开始循环)
3. 内层循环: 该SubLord下的9个SubSubLord (k从j开始循环)
4. 每个SubLord跨度 = (Nakshatra跨度 × Dasha年数) / 120
5. 每个SubSubLord跨度 = (SubLord跨度 × Dasha年数) / 120
6. 当累积度数 >= 目标度数时，返回对应的lords[j]和lords[k]

**其他KP功能**:
- `get_planet_wise_significators()`: 行星级别ABCD significator表
- `get_house_wise_significators()`: 宫位级别ABCD significator表
- `get_consolidated_chart_data()`: 按星座汇总的星盘数据
- `get_transit_details()`: 行运数据含 RL/NL/SL
- `horary_chart.py`: KP Horary上升时间查找算法 (逐秒扫描)

### 依赖
- flatlib: 天文计算 (基于Swiss Ephemeris)
- polars: 数据处理
- timezonefinder, pytz: 时区管理
- prettytable: 表格输出

### 与当前 yinduzhanxing Skill 对比

| 功能 | VedicAstro | 当前 jyotish-vedic-astrology |
|------|-----------|---------------------------|
| KP Sublord | 完整实现 (三段嵌套) | 未实现 |
| KP SubSubLord | 完整实现 | 未实现 |
| KP ABCD Significators | 完整实现 | 未实现 |
| KP Horary | 上升时间查找 + KP_SL_Divisions.csv | 未实现 |
| 基础星盘 | flatlib (Whole Sign/Placidus) | swisseph |
| Vimshottari Dasha | 自建实现 | dashaflow |

---

## 项目3: rishi-ai-mcp (MIT, PyPI v1.1.0)

**仓库**: https://github.com/adarshj322/rishi-ai-mcp
**PyPI**: https://pypi.org/project/rishi-ai-mcp/
**本地路径**: `rishi-ai-mcp/`
**许可证**: MIT License (Copyright (c) 2026 Adarsh J)

### 目录结构
```
rishi-ai-mcp/
├── rishi_ai_mcp.py            # ★ MCP Server 主文件 (223行)
├── test_rishi_ai_mcp.py
├── pyproject.toml
├── LICENSE
├── README.md
├── AGENTS.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── system_prompt.md
├── kilo.json
├── .agents/
│   ├── rules/rishi-ai.md
│   ├── skills/               # 15个 Skill 目录
│   │   ├── career-analysis/SKILL.md
│   │   ├── children-analysis/SKILL.md
│   │   ├── education-analysis/SKILL.md
│   │   ├── finance-analysis/SKILL.md
│   │   ├── full-reading/SKILL.md     # ★ 最完整的分析流程
│   │   ├── geopolitics-analysis/SKILL.md
│   │   ├── health-analysis/SKILL.md
│   │   ├── marriage-analysis/SKILL.md
│   │   ├── muhurtha-analysis/SKILL.md  # ★ Muhurtha 工作流
│   │   ├── past-life-analysis/SKILL.md
│   │   ├── physicalintimacy-analysis/SKILL.md
│   │   ├── relationship-analysis/SKILL.md
│   │   ├── spiritual-analysis/SKILL.md
│   │   └── spouse-profiling/SKILL.md
│   └── workflows/             # 对应每个 Skill 的 workflow 文档
├── .cursor/                   # Cursor IDE 配置
├── .kilo/                     # Kilo IDE 配置
└── .vscode/                   # VS Code 配置
```

### Python 文件

| 文件路径 | 行数 | main函数 | 功能 |
|---------|------|---------|------|
| `rishi_ai_mcp.py` | 223 | L216 `main()` | MCP Server 入口，5个工具 |

### 架构说明

rishi-ai-mcp 是一个 **薄封装层**，核心计算全部委托给 `dashaflow` 库:

```python
from dashaflow import (
    cast_chart,          # cast_vedic_chart 工具
    cast_transit,        # cast_transit_chart 工具 (含 Sade Sati)
    calculate_compatibility,  # calculate_compatibility_tool 工具
    check_muhurtha,      # check_muhurtha_tool 工具
    analyze_career,      # analyze_career_chart 工具
)
```

**5个MCP工具**:
1. `cast_vedic_chart` → `dashaflow.cast_chart()` - 完整出生星盘
2. `cast_transit_chart` → `dashaflow.cast_transit()` - 行运 + Sade Sati
3. `calculate_compatibility_tool` → `dashaflow.calculate_compatibility()` - 16因素合婚
4. `check_muhurtha_tool` → `dashaflow.check_muhurtha()` - 择时评估
5. `analyze_career_chart` → `dashaflow.analyze_career()` - D10职业分析

### Sade Sati 判定逻辑 (位于 dashaflow/vedic_calculator.py) ★★★

```python
# vedic_calculator.py L646-668
sade_sati_active = False
sade_sati_phase = None
dist = (saturn_sign_idx - natal_moon_idx) % 12
if dist == 11:
    sade_sati_active = True
    sade_sati_phase = "rising (12th from Moon)"
elif dist == 0:
    sade_sati_active = True
    sade_sati_phase = "peak (over Moon)"
elif dist == 1:
    sade_sati_active = True
    sade_sati_phase = "setting (2nd from Moon)"
# 输出: { "active": bool, "phase": str, "saturn_transit_sign": str, "natal_moon_sign": str }
```

**Sade Sati三阶段**:
- Phase 1 (上升期): Saturn在月亮星座前一个星座 (第12宫)
- Phase 2 (高峰期): Saturn在月亮星座同宫
- Phase 3 (衰退期): Saturn在月亮星座后一个星座 (第2宫)
- 仅基于月亮星座(sign)判定，不含degree精度

### Muhurtha 选择逻辑 (位于 dashaflow/muhurtha.py) ★★★

**支持的6种活动**: `marriage`, `travel`, `business`, `education`, `house_entry`, `medical`

**每个活动有独立配置**:
- `good_nakshatras`: 吉星宿集合
- `good_tithis`: 吉月相日集合
- `good_lagnas` / `good_weekdays` / `moon_signs`: 条件字段

**评估算法** (`evaluate_muhurtha()`):
1. **Panchang Suddhi** (通用): 排除不吉的Tithi/Nakshatra/Yoga
2. **活动专属Nakshatra检查**: 当前星宿是否在活动吉星宿列表中
3. **活动专属Tithi检查**: 当前月相日是否在活动吉日中
4. **Weekday检查**: 星期是否符合活动要求
5. **Lagna检查**: 上升星座是否在活动吉升星座中
6. **Moon sign检查**: (仅business活动)
7. **婚姻特殊Doshas检查**:
   - Sagraha Dosha: Moon合相任何行星
   - Shashtashta Dosha: Moon在6/8/12宫
   - Bhrigupta Shatka: Venus在6宫
   - Kujaasthama: Mars在8宫
8. **第8宫检查**: (marriage/medical/house_entry) 第8宫不应有行星

**评分**: `score = positive × 10 - negative × 15`
**判定**: auspicious / mixed_favorable / mixed / inauspicious

**Muhurtha SKILL.md 额外规则** (rishi-ai-mcp/.agents/skills/muhurtha-analysis/SKILL.md):
- Tarabala: 行运月亮星宿不能是出生星宿的第3/5/7个Tara
- Chandrabala: 行运月亮不能落在出生月亮星座的6/8/12宫
- Lagna Shuddhi: 行运上升宫不应有凶星
- Gandanta Moon 检查
- Kaal Sarpa 检查

### 与当前 yinduzhanxing Skill 对比

| 功能 | rishi-ai-mcp | 当前 jyotish-vedic-astrology |
|------|-------------|---------------------------|
| Sade Sati | dashaflow 内置 (含三阶段判定) | engine.py 内置 (L409-418, 同样三阶段) |
| Muhurtha | dashaflow 完整实现 (6活动+评分) | 未实现 |
| MCP Server | FastMCP 标准实现 | panchanga_api 有部分实现 |
| 解读Skill | 15个领域SKILL.md | 分散在各模块 |
| 婚姻合盘 | 16因素 Ashtakoot + Kuja Dosha | 部分实现 |
| 职业分析 | D10 + 10宫分析 | 基础分析 |

---

## 可复用代码提取建议

### 优先级最高 ★★★

#### 1. KP Sublord/Subsublord 计算算法
**来源**: VedicAstro/vedicastro/VedicAstro.py L241-288
**方法**: `get_rl_nl_sl_data()`
**可直接复制**: 三段嵌套循环的 KP 经典算法，输入度数输出 RL/NL/SL/SSL
**需要适配**: flatlib → swisseph 天文接口；polars → 标准 Python 数据结构

#### 2. Panchadha Maitri (五重友谊) 尊贵度算法
**来源**: vedic-astro-skills/engine.py L528-596
**方法**: 自建 BPHS Panchadha Maitri 实现
**可直接复制**: NATURAL_REL表 + COMPOUND_TABLE + 判定逻辑
**注意**: 不依赖 dashaflow 的 dignity 模块，是独立实现

### 优先级高 ★★

#### 3. Muhurtha 择时评估系统
**来源**: dashaflow/muhurtha.py (已在 references 中)
**方法**: `evaluate_muhurtha()` + ACTIVITY_RULES
**可直接复用**: 6活动规则字典 + 评分算法 + 婚姻Doshas检查
**可增强**: 集成 rishi-ai-mcp SKILL.md 中的 Tarabala/Chandrabala 规则

#### 4. vedic-core 解读方法论
**来源**: vedic-astro-skills/antigravity/skills/vedic-core/
**价值**: 极详细的 SKILL.md + 5个resource文件
**可复用**:
- house_framework.md: 宫位诊断四维度 + Dasha事件推导硬约束
- p1_p12.md: P1-P12行星审计参数体系
- yogas.md: 24种Yoga定义 + 评估框架 + 赛道合成
- report_rules.md: HTML报告打包规则

### 优先级中 ★

#### 5. rishi-ai-mcp 领域Skill MD
**来源**: rishi-ai-mcp/.agents/skills/ (15个目录)
**价值**: 15个领域的专业占星解读工作流
**亮点**: full-reading/SKILL.md (最完整分析流程), muhurtha-analysis/SKILL.md (择时工作流)

#### 6. KP Horary 上升时间查找
**来源**: VedicAstro/horary_chart.py
**方法**: `find_exact_ascendant_time()` + `KP_SL_Divisions.csv`
**适配工作量大**: 依赖 flatlib 天文库，需迁移到 swisseph

---

## 已有基础对比总结

所有三个项目的核心计算能力(dashaflow)已经存在于 `references/open_source_sources/dashaflow/` 目录中:
- `dashaflow/vedic_calculator.py`: 含 Sade Sati L646-668
- `dashaflow/muhurtha.py`: 完整 Muhurtha 评估系统
- `dashaflow/dignity.py`: 尊贵度计算
- `dashaflow/jaimini.py`: Jaimini Karakas
- `dashaflow/matchmaking.py`: 合婚
- `dashaflow/career.py`: 职业分析

**新获得的增量价值**:
1. **KP Sublord/Subsublord** (VedicAstro) - 核心算法级新增
2. **解读方法论** (vedic-astro-skills) - 人话解读框架级新增  
3. **15个领域 Skill MD** (rishi-ai-mcp) - 工作流级别新增
4. **Panchadha Maitri 自建** (vedic-astro-skills) - 可替代dashaflow依赖
