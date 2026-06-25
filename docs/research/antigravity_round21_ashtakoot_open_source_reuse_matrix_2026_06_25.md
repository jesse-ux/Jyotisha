# Antigravity AI Ashtakoot 开源库直接复用矩阵 (Round 21)

| 项目与 URL | License / 语言 | 可直接复制？ | Ashtakoot 能力 | 风险与 Codex 动作 |
|---|---|---|---|---|
| **VedAstro/VedAstro** | MIT / C# | 🟢 是 (常量表) | 包含 8 Kuta 的极强矩阵。 | **最佳选择**。复制其 36 分常数表。 |
| **VedAstro Python Wrapper** | MIT / Python | 🟢 是 | 通过 API 调用其功能。 | 太重了，只要偷查表常数就行。 |
| **RaviKarrii/Marriage-Compatibility** | MIT / Java | 🟢 是 (逻辑) | Ashtakoot API 计算。 | Java 到 Python 重写成本较低，可参阅其映射。 |
| **alireza-da/pyhora2** | MIT / Python | 🟢 需查验纯净度 | 声称可查合盘。 | 如果真的是 MIT，直接 copy 它的查表 Python 字典。 |
| **RoxyAPI jyotish starter** | MIT / JS | 🟢 是 | 提供 API 范例。 | 只作为 REST JSON 返回体结构的灵感。 |
| **flatlib (Python)** | MIT / Python | 🟢 是 | 星相坐标。 | 不做合盘。可复制其月亮黄经换算。 |
| **VedicAstro (Python)** | MIT / Python | 🟢 是 | 有基础判别。 | 分数粒度不足，只做接口命名参考。 |
| **PyJHora** | AGPL-3.0 | 🛑 **禁止** | 完整 36 分功能。 | **高度传染性**。只允许截它的控制台输出。 |
| **Hora Prakash** | GPL-3.0 | 🛑 **禁止** | 重型计算逻辑。 | 传染性。不看。 |
| **AstroSage (Web)** | 闭源 / Web | 🛑 **禁止** | 业界金标准，有豁免规则。 | 当作 External Oracle 手工抄数验证的靶子。 |

**最小 Codex 改动建议**：优先去找 `VedAstro` 里面的 C# 字典，翻译成 Python 写进 `scripts/ashtakoot_constants.py`。
**推荐搜索指令**：`https://github.com/VedAstro/VedAstro/search?q=Ashtakoot`
