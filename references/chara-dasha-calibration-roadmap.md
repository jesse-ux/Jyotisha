# Chara Dasha 校准路线图

> 目标：从 24.17% 匹配 KN Rao 基准提升至 >80%
> 版本：v6.9.8 | 更新：2026-06-13

---

## 问题诊断

### 当前实现（v6.1.12）
- **方法**：KN Rao Method — 序列基于第9宫方向判定，时长基于宫主所在宫位+尊贵调整
- **基准**：PyJHora 10案例×12星座 = 120对（Sign 100%, Dur 91.67%, **Overall 95.83%**）
- **问题**：KN Rao 基准通过率仅 24.17%（feature-gap-matrix）

### 根因分析
1. **序列方向判定逻辑**：Chara Dasha 的起始星座由第9宫方向（顺时针/逆时针）决定，此处容易出错
2. **尊贵权重调整**：行星所在星座的尊贵等级对时间长度的影响系数需要精确校准
3. **Antardasha 等分 vs 非等分**：当前实现等分12份，但部分经典建议按行星尊贵加权
4. **双星同宫处理**：两个行星在同一星座时的序列判定规则

### 数据源
- **PyJHora Chara Dasha 输出**（可作为 ground truth）
- **KN Rao《Predicting through Jaimini's Chara Dasha》**
- **Sanjay Rath《Jaimini Upadesa Sutras》**
- **PVR Narasimha Rao JHora 输出**（最终验证）

---

## 校准步骤

### Phase 1: 基准数据采集（即刻）
1. 运行 PyJHora 对 16 个名人案例生成 Chara Dasha 时间线
2. 运行 yinduzhanxing 对同样案例生成当前 Chara Dasha
3. 对每对输出：比对星座序列、时间长度、Antardasha 分配
4. 生成差异矩阵 → 识别系统偏差模式

### Phase 2: 根因修复（1-2天）
5. 修复星座序列判定逻辑（第9宫方向的精确计算）
6. 修复时间长度计算（宫主尊贵权重校准）
7. 修复 Antardasha 非等分（按尊贵加权而非等分12份）
8. 每步修复后与 PyJHora 基准对比

### Phase 3: 精确度提升（持续）
9. 引入双星同宫处理规则
10. 加入 Prana/Antardasha 微调
11. 与 JHora 最终验证（≥5案例）
12. 建立 30+ 案例基准集

---

## 关键代码位置

| 模块 | 文件 | 函数 |
|------|------|------|
| Jaimini 系统 | `scripts/jaimini.py` | `calculate_chara_dasha()` |
| KN Rao 序列 | `scripts/jaimini.py` | `_chara_dasha_sequence()` |
| 时间长度 | `scripts/jaimini.py` | `_chara_dasha_duration()` |
| Dasha 计算器 | `scripts/dasha_calculator_enhanced.py` | Chara Dasha 集成 |
| 全盘解读 | `scripts/jyotish_engine.py` | `cmd_full_reading()` |

---

## 验收标准

| 阶段 | 基准 | 目标 |
|------|------|------|
| Phase 1 | — | 基准数据采集完成 |
| Phase 2 | PyJHora | Sign 100%, Duration >90%, Overall >85% |
| Phase 3 | JHora | Sign 100%, Duration >95%, Overall >90% |
| 最终 | 30 案例自有基准 | Chara Dasha 事件应期反推 >80% |
