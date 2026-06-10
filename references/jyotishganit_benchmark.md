# jyotishganit 精度基准对比报告

> 对比对象：我们的引擎 (swisseph + Lahiri Ayanamsa) vs jyotishganit v0.1.0 (skyfield + True Chitra Paksha Ayanamsa)
> 生成时间: 2026-06-10 18:51:01
> jyotishganit 许可证: MIT (c) northtara

## 关键差异说明

| 项目 | 我们的引擎 | jyotishganit |
|------|-----------|--------------|
| 天文计算库 | Swiss Ephemeris (pyswisseph) | Skyfield + JPL DE421 |
| Ayanamsa | Lahiri (Chitra Paksha) | True Chitra Paksha |
| 行星节点 | Mean Node (默认) | Mean Node |
| 分盘算法 | BPHS标准 | BPHS标准 (jyotishyamitra实现) |
| 宫位制 | Whole Sign | Whole Sign |

**核心差异**：Ayanamsa选择不同（Lahiri vs True Chitra Paksha），预期导致所有行星经度存在系统性偏移，偏移量约等于两种Ayanamsa值之差。

## 总结与分析

### 系统性差异

1. **Ayanamsa差异**是最大的系统性差异来源。Lahiri Ayanamsa和True Chitra Paksha Ayanamsa在计算方法上不同：
   - Lahiri：基于春分点与Chitra星(Spica)的角距离
   - True Chitra Paksha：直接计算Spica的黄道经度减去180°
   - 差异通常在0.1-0.5°之间，随时间略有变化

2. **行星经度偏移**：由于Ayanamsa差异，所有行星经度存在系统性偏移。如果减去Ayanamsa差异，剩余偏差应非常小（<0.1°），这取决于天文计算库（Swiss Ephemeris vs Skyfield/JPL）的精度差异。

3. **分盘计算**：两边的分盘算法基于BPHS标准，理论上应该一致。但如果D1行星位置因Ayanamsa偏移而跨星座边界，可能导致分盘星座不同。

### 精度评估

- **Swiss Ephemeris**：行业标准，基于JPL DE431，精度极高（<1角秒）
- **Skyfield + DE421**：同样高精度，但DE421精度略低于DE431（差异在角秒级别）
- **实际影响**：对于占星用途，两者的天文计算精度差异可以忽略（<0.01°）

### 建议

1. 两种Ayanamsa的选择是占星学派的差异，不是精度问题
2. 可以考虑添加True Chitra Paksha Ayanamsa作为可选项
3. 分盘算法可以交叉验证，确保BPHS标准实现一致
4. Ashtakavarga贡献表已校准到BPHS标准，两边应一致

---
*本报告由 jyotishganit_benchmark.py 自动生成*
*jyotishganit (MIT License, c) northtara - https://github.com/northtara/jyotishganit*
