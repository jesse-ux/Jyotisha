# Antigravity AI Codex Round 24 执行计划 (Round 23)

根据目前的引擎兼容状态与空白字典状态，建议 Codex 立刻执行以下前 15 步：

1. **[Git Push]** `git add docs/research/antigravity_round23*`，然后 `git commit` 并 `git push origin codex/release-hygiene-ci`，保住这 16+ 份深核战报。
2. **[移除冗余]** 既然 API 已经无缝切换到 `ashtakoot.py`，请在 `synastry.py` 文件顶部加上 `# DEPRECATED` 警告，并择机清理测试里对其的依赖。
3. **[建立常数文件]** 新建 `scripts/ashtakoot_constants.py`。
4. **[联网扒常数]** 登录 GitHub，定位 `VedAstro/VedAstro`。
5. **[洗数据]** 将 VedAstro 的 27 宿 Nadi 分组、14 种 Yoni 动物冲突矩阵，手写或用脚本转换为 Python Dict。
6. **[引入常数]** 在 `ashtakoot.py` 中 `import ashtakoot_constants`。
7. **[替换伪代码]** 把原来写死为 0 的 `varna`, `tara` 全部替换为从 Dict 里查值。
8. **[更新总分]** 更新 `total_score` 为 8 个 Kuta 的 sum。
9. **[写测试]** 在 `test_ashtakoot.py` 加一个断言 `ashwini` 和 `ashwini` 配对是 36 分的 assert。
10. **[加 Kuja 枚举]** 去 `oracle_evidence_validator.py` 加上对 `kuja_status` 为 `"no_dosha"` 等 4 个 Enum 的验证。
11. **[加 Shadbala 阈值]** 去 Validator 给所有星的 Shadbala rupa 值加上 `< 20.0` 的门限。
12. **[加 AI 进度]** 去 `jyotish_engine.py` 把 `ashtakoot_oracle_progress` 合并进返回里。
13. **[ provenance ]** 在 API 返回里挂上 `source_license: "MIT"`。
14. **[前端适配]** 改前端 Trust Center，一分为二，各自显示大运和合婚的 0/5 进度条。
15. **[等待人类]** 催着操作员交那份 JHora 截图 JSON。

**不做事项**：千万别在 `ashtakoot.py` 里写几百行的 if/else，必须把字典查表干净地拆分到 `_constants.py` 里。
