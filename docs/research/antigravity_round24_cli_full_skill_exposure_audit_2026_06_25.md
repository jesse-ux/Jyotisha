# Antigravity AI CLI 全技能暴露度审计 (Round 24)

| 检查项 | CLI 脚本名 | 状态与用户友好度 |
|---|---|---|
| 1. 核心计算引擎 | `jyotish_engine.py` | 🟢 提供 `--mode json`, `--mode text`，非常友好。 |
| 2. 准确率报告 | `local_accuracy_report.py`| 🟢 提供 `--format json`, `--format markdown`，非常友好。 |
| 3. 质量门禁 | `run_quality_gate.py` | 🟢 `--profile quick` 设计绝佳。 |
| 4. Jaimini Dasha | `chara_dasha.py` | 🟡 缺乏直观的 `--help` 参数说明。 |
| 5. Ashtakavarga | `ashtakavarga_v2.py` | 🟡 主要是内部调用，直接运行报错缺入参。 |
| 6. Solar Return | `varshaphala.py` | 🟡 同上，极客向。 |
| 7. Synastry | `ashtakoot.py` | 🟡 可单独跑，但传参困难 (需传入月亮经度)。 |
| 8. PWA/Desktop 前置 | `deployment_preflight.py`| 🟢 一眼看出各类前端环境是否完备。 |
| 9. Oracle 检查 | `oracle_evidence_validator.py`| 🟢 强校验，开发者必备。 |
| 10. 隐私清理 | `privacy_sweep.py` | 🟢 极好。 |
| 11. BPHS 验证 | `validate_bphs_invariants.py`| 🟢 极好。 |
| 12. 真人测试 | `run_real_case_revalidation.py`| 🟢 极好。 |
| 13. README 文档 | 部分涵盖 | 只涵盖了 engine，其他脚本无文档说明。 |
| 14. 接到 Web 难易度 | 无需接 | 因为有独立的 API Server。 |
| 15. argparse 使用 | 不统一 | 很多旧的脚本还在用 sys.argv 裸奔。 |
| 16. 下一步建议 | 统一 | 全面改写为 `argparse` 标准化入参。 |

**副手下一轮任务**：梳理所有 CLI 中没用 `argparse` 的野鸡脚本。
**Codex 可做任务**：在 README 中加一段关于 `chara_dasha.py` 单独调用的命令示例。
