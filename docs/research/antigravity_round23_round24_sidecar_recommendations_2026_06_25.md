# Antigravity AI Round 24 副手任务建议 (Round 23)

为下一轮（Round 24）副手提供以下 30 项并行的黑盒审计与设计任务：

1. **目标**: 确认 Codex 是否成功 Push 本轮的 16+ 份报告。**读取**: `git log`。**输出**: `git_push_audit.md`。
2. **目标**: 提取 VedAstro 库 `MatchCalculator.cs` 中的 `CalculateVarna` 的核心 if/else 分支。**联网**: VedAstro。**输出**: `varna_extraction_logic.md`。
3. **目标**: 提取 `CalculateVashya` 常量。**联网**: VedAstro。**输出**: `vashya_extraction_logic.md`。
4. **目标**: 提取 `CalculateTara` 常量。**联网**: VedAstro。**输出**: `tara_extraction_logic.md`。
5. **目标**: 提取 `CalculateYoni` 矩阵 (14x14)。**联网**: VedAstro。**输出**: `yoni_extraction_logic.md`。
6. **目标**: 提取 `CalculateGrahaMaitri` 敌友矩阵。**联网**: VedAstro。**输出**: `grahamaitri_extraction_logic.md`。
7. **目标**: 提取 `CalculateGana` 矩阵。**联网**: VedAstro。**输出**: `gana_extraction_logic.md`。
8. **目标**: 提取 `CalculateBhakoot` 逻辑。**联网**: VedAstro。**输出**: `bhakoot_extraction_logic.md`。
9. **目标**: 提取 `CalculateNadi` 与相同星宿例外豁免规则。**联网**: VedAstro。**输出**: `nadi_extraction_logic.md`。
10. **目标**: 设计一份能够自动将上述逻辑拼接为 Python `dict` 的转换脚本。**输出**: `csharp_to_python_converter_design.md`。
11. **目标**: 审计目前 `tests/test_api_server_security.py` 中的 coverage。**运行**: `pytest`。**输出**: `api_security_coverage.md`。
12. **目标**: 复盘 `mangal_dosha` 是否可以直接给 `kuja_status` 供数。**读取**: `scripts/yogas_doshas/`。**输出**: `mangal_dosha_reuse.md`。
13. **目标**: 确认 Playwright 截图是否被加入 `.gitignore`。**读取**: `.gitignore`。**输出**: `playwright_artifacts_ignore.md`。
14. **目标**: 测试目前 API 在 0 经度和 360 经度的边缘。**运行**: `pytest`。**输出**: `degree_boundary_tests.md`。
15. **目标**: 设计基于 JSON Schema 的 Validator 重构方向。**读取**: `oracle_evidence_validator.py`。**输出**: `json_schema_validator_proposal.md`。
16. **目标**: 拟定多语言切换的翻译表 JSON 结构。**输出**: `i18n_schema_design.md`。
17. **目标**: 分析 `jyotish-app/package.json` 中的遗留过时依赖。**读取**: `package.json`。**输出**: `npm_dependencies_audit.md`。
18. **目标**: 为 `Trust Center` 撰写中文帮助气泡文案。**输出**: `trust_center_tooltips.md`。
19. **目标**: 构思基于 Vite PWA 插件的离线缓存。**读取**: `vite.config.js`。**输出**: `vite_pwa_caching.md`。
20. **目标**: 复核所有 `.py` 文件是否都包含 UTF-8 声明。**命令**: `rg`。**输出**: `utf8_declaration_audit.md`。
21. **目标**: 设计一个供操作员直接访问的 PWA 合婚打分对比页。**输出**: `comparator_page_design.md`。
22. **目标**: 分析 Astrox (Rust) 库对合婚的可能性。**联网**: GitHub。**输出**: `astrox_synastry_feasibility.md`。
23. **目标**: 制定对 5 个 Validator Draft JSON 的 Mock 数据填充计划。**输出**: `validator_mock_filling_plan.md`。
24. **目标**: 检查 README.md 中是否遗漏 Ashtakoot 功能说明。**读取**: README。**输出**: `readme_ashtakoot_update.md`。
25. **目标**: 为 D9 盘渲染构思类似 Ashtakavarga 的散点图。**输出**: `d9_scatter_plot_design.md`。
26. **目标**: 设计 `target.shadbala_totals` 的测试。**输出**: `shadbala_totals_test_design.md`。
27. **目标**: 梳理 API 失败重试机制。**输出**: `api_retry_mechanism.md`。
28. **目标**: 审计 Python 代码复杂度。**运行**: `radon` (若有)。**输出**: `cyclomatic_complexity.md`。
29. **目标**: 构思对旧版本 `synastry.py` 中引用的安全废除。**输出**: `synastry_deprecation_plan.md`。
30. **目标**: 汇总 Round 24 副手最终建议。**输出**: `round24_final_summary.md`。
