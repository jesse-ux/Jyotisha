# Antigravity AI Codex Round 25 实施 Backlog (Round 24)

请 Codex 接下来像绞肉机一样执行以下高 ROI 开发包（摘录 60 个中最重要的 15 个）：

1. [文件: `docs/research`] `git commit -m "docs(research): round 24 artifacts"`，保护现场！
2. [文件: `ashtakoot_constants.py`] 新建文件，用手敲或者脚本生成方式，注入 VedAstro 的 27 宿 Nadi 分组与判定函数。
3. [文件: `ashtakoot_constants.py`] 注入 Yoni 14 种动物的冲突矩阵 `14x14 list`。
4. [文件: `ashtakoot_constants.py`] 注入 Gana 矩阵。
5. [文件: `ashtakoot_constants.py`] 注入 Bhakoot (星座距离) 计分。
6. [文件: `ashtakoot_constants.py`] 注入 Graha Maitri (星体敌友) 计分。
7. [文件: `ashtakoot_constants.py`] 注入 Tara (星宿距离) 计分。
8. [文件: `ashtakoot_constants.py`] 注入 Vashya 计分。
9. [文件: `ashtakoot_constants.py`] 注入 Varna 计分。
10. [文件: `ashtakoot.py`] 全面废弃旧的 `0` 返回，挂上 `total_score` 的动态求和。
11. [文件: `jyotish-app/main.js`] 将 Trust Center 中的 Dasha 卡片和 Ashtakoot 卡片左右物理拆分。
12. [文件: `oracle_evidence_validator.py`] 给 Shadbala 的 7 大星加上 `< 20 Rupa` 的天花板。
13. [文件: `oracle_evidence_validator.py`] 给 Kuja 加上 Enum ("no_dosha", "mild_dosha" 等)。
14. [文件: `jyotish_api_server.py`] 返回的字典里植入 `{"source_project": "VedAstro", "license": "MIT"}`。
15. [文件: `tests/test_ashtakoot.py`] 加入一对 `Ashwini` 碰 `Ashwini` 的测试，断言分数为 36 或 33（根据例外规则）。

**验收**：所有测试通过，`pytest tests/test_ashtakoot.py` 大绿。
