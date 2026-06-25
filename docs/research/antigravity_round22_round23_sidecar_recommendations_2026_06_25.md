# Antigravity AI Round 23 副手任务建议 (Round 22)

在 Round 23 中，我（副手）将继续承担高体量、低耦合并行的审计和设计。以下是 25 条拆解：

1. **目标**: 审计 `scripts/jyotish_api_server.py` 对 Ashtakoot `/api/synastry` 的全覆盖。**命令**: `rg synastry scripts/`。**报告**: `api_synastry_audit.md`。**不可做**: 不写业务代码。
2. **目标**: 检查 `test_ashtakoot.py` 中的伪覆盖情况。**命令**: `pytest tests/test_ashtakoot.py -v`。**报告**: `ashtakoot_test_debt.md`。
3. **目标**: 设计 Kuja Dosha (Manglik) 状态的 UI 展示规范。**读取**: `jyotish-app/src/components/Ashtakoot.vue`。**报告**: `kuja_dosha_ui_spec.md`。
4. **目标**: 设计 5 个 Ashtakoot 合婚 Oracle 样例包的值。**读取**: `references/oracle/ashtakoot_oracle_cases.json`。**报告**: `ashtakoot_oracle_mock_design.md`。
5. **目标**: 写出 VedAstro 常量提取的 Python 脚本草稿。**读取**: Github VedAstro 源码 URL。**报告**: `vedastro_extraction_script_draft.md`。
6. **目标**: 审查 `jyotish-app/main.js` 现有的 Error Handler。**读取**: `jyotish-app/main.js`。**报告**: `error_handler_ux_audit.md`。
7. **目标**: 分析 36 分评判标准对印度北/南派的差异。**联网**: 查阅 Ashtakoot vs Dasakoot。**报告**: `ashtakoot_regional_difference.md`。
8. **目标**: 检查 D9 (Navamsa) 同步信息在 API 中的透传。**读取**: `scripts/jyotish_engine.py`。**报告**: `navamsa_sync_audit.md`。
9. **目标**: 制定 Playwright 安装与基建脚手架方案。**读取**: `package.json`。**报告**: `playwright_scaffolding_plan.md`。
10. **目标**: 审查所有 `docs/research/` 历史文件的冗余。**命令**: `ls -lh docs/research/`。**报告**: `research_docs_redundancy.md`。
11. **目标**: 设计 `target.shadbala_totals` 的测试用例。**读取**: `tests/test_oracle_evidence_validator.py`。**报告**: `shadbala_totals_tests_design.md`。
12. **目标**: 确认 AstroSage 的打分和 VedAstro 的打分是否严格等价。**联网**: 验证 36 分标准。**报告**: `astrosage_vedastro_parity.md`。
13. **目标**: 扫描 `scripts/` 中所有的 `TODO:` 或 `FIXME:` 标签。**命令**: `rg TODO scripts/`。**报告**: `todo_fixme_audit.md`。
14. **目标**: 设计 PWA Manifest 和 Desktop Icons 结构。**读取**: `jyotish-app/index.html`。**报告**: `pwa_manifest_design.md`。
15. **目标**: 审查 `run_quality_gate.py` 能否加入 Playwright 测试。**读取**: `scripts/run_quality_gate.py`。**报告**: `quality_gate_playwright_integration.md`。
16. **目标**: 分析 Trust Center UI 如何兼容多语言 (i18n)。**读取**: `jyotish-app/main.js`。**报告**: `trust_center_i18n_plan.md`。
17. **目标**: 梳理 AI Prompt Pack 的 Token 占用峰值。**命令**: `python3 scripts/jyotish_engine.py --mode full`。**报告**: `prompt_pack_token_cost.md`。
18. **目标**: 为 Validator 增加 `kuja_status` 错误码映射表。**读取**: `scripts/oracle_evidence_validator.py`。**报告**: `kuja_status_error_mapping.md`。
19. **目标**: 验证 `.gitignore` 是否拦截了 Playwright 的视频产物。**读取**: `.gitignore`。**报告**: `playwright_gitignore_audit.md`。
20. **目标**: 分析当前 `Ashtakoot` 调用的月亮度数计算是否有精度漂移。**读取**: `scripts/ashtakoot.py`。**报告**: `moon_longitude_precision.md`。
21. **目标**: 制定一套“模拟 JHora 输出”的 Mock 测试脚本。**命令**: 无。**报告**: `jhora_mock_generator.md`。
22. **目标**: 分析 `jyotish-app` 中 Tailwind CSS (若有) 或原生 CSS 的冗余。**读取**: `jyotish-app/index.css`。**报告**: `css_redundancy_audit.md`。
23. **目标**: 调查 Tauri 打包在 Mac 和 Windows 上的证书签名机制。**联网**: 查阅 Tauri docs。**报告**: `tauri_code_signing.md`。
24. **目标**: 复盘本仓库从 Draft 到 Production 的核心流转图。**读取**: README。**报告**: `state_machine_diagram.md`。
25. **目标**: 汇总 Round 23 最终结论。**命令**: `git status`。**报告**: `round23_final_summary.md`。
