# Antigravity AI Ashtakoot Constants 数据结构设计 (Round 22)

设计 `scripts/ashtakoot_constants.py`：

1. **文件职责**：只负责存放字典与查表函数，不包含具体请求逻辑。
2. **常量命名**：`NAKSHATRA_NADI_MAPPING`, `VASHYA_SCORE_MATRIX`。
3. **枚举**：把 27 宿定义成 `Enum`。
4. **8 Kuta 表结构**：使用二维字典或 `Tuple[int, int]` 作为 key 的扁平字典。例如 `{(1, 2): 7}`。
5. **源项目 attribution**：顶部声明 `# Constants derived from VedAstro (MIT License)`.
6. **provenance 字段**：可在返回的 JSON 里加上 `_source: "VedAstro Algorithm"`。
7. **测试 helper**：暴露 `get_varna_score(boy_moon, girl_moon)` 供单元测试调用。
8. **运行时依赖**：无。纯 Python dict。
9. **与 `ashtakoot.py` 接口**：`ashtakoot.py` 导入它，算出 8 个值后打包成 JSON。
10. **JSON vs Python dict**：用纯 `.py` 字典性能最高，且方便加注释。
11. **边界 case**：对于没找到的组合，抛出 `ValueError`。
12. **Codex 最小实现步骤**：从 VedAstro 复制出 C# 代码，让大模型将其转换为纯粹的 Python 字典。
