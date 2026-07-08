---
name: jyotish-engine-modules
description: 印度占星排盘引擎历史模块集成说明（供审计与迁移参考，当前真源以主 SKILL.md 与 registry 为准）
version: 1.0.0
author: 助手
tags: [jyotish, vedic-astrology, calculation-engine, karaka, special-lagnas, vimsopaka, avastha, divisional-charts]
related_skills: [jyotish-full-reading-integration, jyotish-vedic-astrology]
---

# 印度占星排盘引擎历史模块说明

本 skill 记录了 5 个核心计算模块的历史集成背景，主要用于审计、迁移和对照旧工作流。

本 Skill 的 `scripts/` 副本仅作为独立分发包与历史迁移参考；主仓当前计算真源、成熟度判断、外部 oracle 边界和发布口径一律以主 `SKILL.md`、`references/technique_registry.json` 与主仓测试为准。

当前项目的唯一对外真源以以下文件为准：

1. `<repo>/SKILL.md`
2. `<repo>/references/technique_registry.json`
3. `<repo>/references/strict-workflow-router.md`

本文件不得单独作为“当前能力完整性”依据；若与主 skill 描述冲突，以主 skill 与 registry 为准。

## 当前使用边界

本文件的定位是：

1. 说明历史模块曾如何并入主仓
2. 便于审计、迁移、回收旧碎片
3. 为“是否已有实现可复用”提供线索

本文件**不是**当前 skill 完成度、成熟度或精度闭环的直接依据。

## 判断原则（与主 skill 保持一致）

1. 若主仓 `scripts/`、`references/`、`skills/` 已有主体实现，优先判断为“补成熟度/补入口”，不要在旧模块层面重写。
2. 若外部来源是 MIT / Apache / BSD，可优先考虑复用结构、常数、映射与文档资产；GPL / AGPL / 闭源仅允许黑盒对照。
3. 涉及 `Dasha` 精确边界、`Shadbala` 绝对值、传统软件口径冻结时，必须以外部 oracle 闭环为准，不能仅凭历史模块说明认定“已完成”。
4. 若本文件的历史调用链与主仓当前真相源不一致，以主仓真相源为准，不沿用旧版本表述。

## 历史模块清单

1. **karaka_calculator.py** - Karaka分配计算器（支持BPHS/JH兼容模式）
2. **special_lagnas.py** - 特殊上升点计算（Bhava/Hora/Ghati Lagna等）
3. **vimsopaka_calculator.py** - Vimsopaka Bala分盘力量计算
4. **avastha_calculator.py** - Avasthas行星状态计算（年龄/警觉/情绪）
5. **divisional_charts_extended.py** - D2-D60完整分盘宫位图

## 使用方法

### 1. 创建本地工作目录

```bash
mkdir -p ~/Projects/yinduzhanxing-local/scripts
cd ~/Projects/yinduzhanxing-local
```

### 2. 复制模块代码

从本skill的 `scripts/` 目录复制5个Python文件到本地工作目录。

### 3. 同步到GitHub

```bash
# 克隆GitHub仓库
cd ~/Projects
git clone https://github.com/732642856/yinduzhanxing.git
cd yinduzhanxing

# 复制新模块
cp ~/Projects/yinduzhanxing-local/scripts/*.py ./scripts/

# 提交并推送
git add scripts/
git commit -m "feat: 新增5个核心排盘引擎模块

- karaka_calculator.py: Karaka分配计算器（BPHS/JH兼容模式）
- special_lagnas.py: 特殊上升点计算
- vimsopaka_calculator.py: Vimsopaka Bala分盘力量
- avastha_calculator.py: Avasthas行星状态
- divisional_charts_extended.py: D2-D60完整分盘"

git push origin main
```

## 模块详细说明

### 1. karaka_calculator.py

**核心功能：**
- 计算Jaimini Chara Karaka（7大可变象征星）
- 支持3种模式：
  - BPHS 8-Karaka（标准）
  - BPHS 7-Karaka（不含Rahu）
  - JH兼容模式（Rahu限制在MK）

**关键特性：**
- 自动识别Karaka模式
- 星座内度数排序（0-30度）
- 详细的Karaka象征意义
- 完整的验证机制

**命令行使用：**
```bash
python3 scripts/karaka_calculator.py --mode bphs --planets "Sun:45.5,Moon:120.3,Mars:200.1,Mercury:50.8,Jupiter:180.5,Venus:90.2,Saturn:250.7,Rahu:150.4"
```

### 2. special_lagnas.py

**核心功能：**
- Bhava Lagna（宫位上升）
- Hora Lagna（时辰上升）
- Ghati Lagna（Ghati上升）
- Arudha Lagna（映像上升）
- Upapada Lagna（配偶映像上升）

**计算公式：**
- Bhava Lagna = Asc + (Sun - Moon)
- Hora Lagna = Asc + (Sun位置 × 时间因子)
- Ghati Lagna = 基于Ghati单位的上升点推进

### 3. vimsopaka_calculator.py

**核心功能：**
- 16分盘权重系统（Shodasavarga）
- Varga Dignity尊严等级判定
- 分盘综合力量评分
- Vimsopaka Bala总分计算

**权重体系：**
- D1 (Rasi): 3.5
- D2 (Hora): 1.0
- D3 (Drekkana): 1.0
- D9 (Navamsa): 3.5
- D12 (Dwadasamsa): 0.5
- ... (共16个分盘)

### 4. avastha_calculator.py

**核心功能：**
- Bala Avastha（年龄状态）：婴儿/少年/青年/老年/死亡
- Jagrat Avastha（警觉状态）：清醒/梦境/深睡
- Deeptadi Avastha（情绪状态）：15种状态

**判定规则：**
- 基于行星度数位置
- 基于行星与其他行星的关系
- 基于行星在星座中的位置

### 5. divisional_charts_extended.py

**核心功能：**
- D1-D60完整计算
- 每个分盘的12宫位行星分布
- 分盘上升点精确计算
- 分盘宫位图可视化输出

**支持的分盘：**
- D1-D12（基础分盘）
- D16, D20, D24, D27, D30（特殊分盘）
- D40, D45, D60（高级分盘）

## 集成到主引擎

在 `jyotish_engine.py` 中导入这些模块：

```python
from karaka_calculator import KarakaCalculator, KarakaMode
from special_lagnas import SpecialLagnasCalculator
from vimsopaka_calculator import VimsopakaBalaCalculator
from avastha_calculator import AvasthaCalculator
from divisional_charts_extended import DivisionalChartsCalculator
```

> **注意**：这 5 个模块现已并入主仓库维护。本 Skill 的 `scripts/` 副本只作为历史分发包/迁移参考，不代表当前能力边界。
> **AI Native 注意**：主仓库 `full-reading` 与 `/api/chart` 已输出 `ai_prompt_pack` 和 Ayanamsa 元数据；独立分发时若调用主引擎，应优先消费这些字段作为解读上下文，不要在 Raman/KP 等非 Lahiri 设置下硬编码默认口径。

## 验证测试

```bash
# 测试Karaka计算器
python3 scripts/karaka_calculator.py --mode bphs

# 测试特殊上升点
python3 scripts/special_lagnas.py --asc 45.5 --sun 120.3 --moon 200.1

# 测试Vimsopaka
python3 scripts/vimsopaka_calculator.py --planet Sun --d1 Aries --d9 Leo

# 测试Avastha
python3 scripts/avastha_calculator.py --planet Sun --degree 15.5

# 测试分盘
python3 scripts/divisional_charts_extended.py --asc 45.5 --divisions all
```

## 注意事项

1. **Karaka模式选择**：
   - 与Jagannatha Hora保持一致时使用 `--mode jh`
   - 标准BPHS使用 `--mode bphs`

2. **精度要求**：
   - 所有度数计算精确到小数点后4位
   - 分盘计算使用Swiss Ephemeris标准

3. **依赖项**：
   ```bash
   pip install swisseph numpy
   ```

4. **性能优化**：
   - 分盘计算支持批量模式
   - 缓存机制减少重复计算

## 更新日志

### v1.0.0 (2026-05-03)
- 初始版本
- 5个核心模块完整实现
- 支持命令行和Python API两种调用方式
