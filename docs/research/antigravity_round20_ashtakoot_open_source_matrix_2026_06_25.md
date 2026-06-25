# Antigravity AI 开源 Ashtakoot 可复用矩阵 (Round 20)

深入检索全球 15 个合婚开源库，结论如下：

### 第一阵营：MIT/Apache/BSD（直接可用候选）
| 项目与 URL | 语言/License | 活跃度 | 核心合婚要素提取 | 风险 | Codex 动作 |
|---|---|---|---|---|---|
| **VedAstro** (/VedAstro) | C#/JS (MIT) | 极高 | 拥有最全的 36 分 Kuta 查表数组。 | 需把 C# 数组转换为 Python dict。 | **必抄**：全盘复制它的 8 Kuta 基础映射数组。 |
| **AstroMatch** (GitHub) | Python (MIT) | 中 | Nakshatra 匹配度的简单逻辑。 | 缺乏 Nadi Dosha 异常豁免。 | 参考其数据解包逻辑。 |
| **flatlib** (/flatlib) | Python (MIT) | 低 | 星体类与位置计算。 | 没有 Ashtakoot。 | 提取月亮计算做快算。 |
| **panchanga** | Python (MIT) | 高 | Dina, Tara 等历法运算。 | 体系过重，依赖复杂。 | 剥离 Tara 计算逻辑。 |
| **VedicAstro** | Python (MIT) | 低 | 有简单的星座匹配逻辑。 | 分数只有总分没有明细。 | 只看它 Python 命名规范。 |

### 第二阵营：GPL/AGPL/商业（只能参考行为）
| 项目与 URL | 语言/License | 活跃度 | 核心行为参考点 | 风险 | Codex 动作 |
|---|---|---|---|---|---|
| **PyJHora** | Python (AGPL) | 高 | JHora 合盘模块重写版。 | 严重传染性，看一眼都不行。 | **严禁复制**，只用 CLI 输出对数。 |
| **Maitreya** | C++ (GPL) | 停滞 | 古典合盘豁免规则（Exception）。 | 传染性。 | 只提取其“木星豁免”文献思路。 |
| **AstroSage** | Web (闭源) | 商业 | `Kuja Dosha` 叠加判定机制。 | 商业维权。 | 测试时用它做验证基准。 |
| **JHora** | Desktop (闭源) | 稳定 | Asthakoot 权威终极答案。 | 不可反编译。 | 填 JSON 做外部数据包。 |
| **HinduVahini** | App (闭源) | 活跃 | 印度语本地化术语表。 | 无代码可抄。 | 获取合婚相关名词翻译。 |

**落地建议**：Codex 唯一能大胆去抄的就是 `VedAstro` 里面的数组常量。这是我们快速构建 `scripts/ashtakoot.py` 最合规、最安全的路径。
