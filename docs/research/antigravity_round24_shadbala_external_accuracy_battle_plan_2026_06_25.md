# Antigravity AI Shadbala 外部校准作战包 (Round 24)

| 样本名称/测试目的 | 验证细节 | JHora 截图目标 | 晋级判据 |
|---|---|---|---|
| 1. Sthana Bala (位置力量) | 7 星 | Strength 面板 Sthana 行 | 容差 < 0.1 Rupa |
| 2. Dig Bala (方向力量) | 7 星 | Dig Bala 行 | 容差 < 0.1 Rupa |
| 3. Kala Bala (时间力量) | 7 星 | Kala Bala 行 | 容差 < 0.1 Rupa |
| 4. Chesta Bala (逆行力量) | 7 星 | Chesta Bala 行 | 容差 < 0.1 Rupa |
| 5. Naisargika Bala (自然力量) | 7 星 | Naisargika Bala 行 | 常数比较，完全一致 |
| 6. Drik Bala (相位力量) | 7 星 | Drik Bala 行 | 容差 < 0.2 Rupa (相位极易分歧) |
| 7. 总 Rupa 核对 | 7 星总和 | Total Rupa 行 | 必须等同于六项和 |
| 8. JHora vs VedAstro 差异 | 对比同一出生资料 | 网页 vs JHora | 容差度量 |
| 9. 白天出生极值 | 测 Kala Bala 的太阳 | 某盘 | 太阳 Kala 极高 |
| 10. 夜间出生极值 | 测 Kala Bala 的月亮 | 某盘 | 月亮 Kala 极高 |
| 11. 强逆行极值 | 测 Chesta Bala | 多星逆行盘 | 逆行分数飙高 |
| 12. 满月极值 | 测 Paksha Bala (含于 Kala) | 满月出生盘 | 月亮附加分极高 |
| 13. Virupa 单位验证拦截 | 确保无人录入 Virupa | 故意填 Virupa | 被 Validator 拒绝 |
| 14. 极光极夜出生 | 测 Dig Bala 异常 | 北极圈出生 | 是否抛错或返回合理值 |
| 15. 最小 Rupa | 弱星底线 | 落陷且被克制 | 分数必须 > 0 |
| 16. 何时允许生产调参 | 门槛条件 | 满 5/5 Valid Packets | 允许解锁机器学习脚本 |

**副手下一轮任务**：从 VedAstro 源代码挖掘 Kala Bala 计算公式。
**Codex 可做任务**：在 UI 上明确标出 Rupa，警示用户不要错看成 Virupa 录入。
