# Antigravity AI Round 23 最终汇总与 Round 24 建议

### 1. 本轮新增报告列表
本轮共生成了 A 到 P 计 16 份精准评估报告：
(A) API Full Engine Blackbox, (B) Synastry Retirement Decision, (C) Frontend Compatibility, (D) Round 22 Archive Strategy, (E) MIT Constants Source Recheck, (F) Ashtakoot Provenance Design, (G) Oracle Progress Integration, (H) Kuja Status Enum, (I) Shadbala Unit Acceptance, (J) JHora Operator Brief, (K) Ashtakoot Capture Brief, (L) Playwright Minimal Plan, (M) Push Readiness Second Audit, (N) Round 24 Sidecar Recs, (O) Codex Round 24 Plan, (P) Final Summary.

### 2. 每个工作包一句话结论
- A: API 切完整 Ashtakoot 引擎极其顺滑，测试全绿，连原有的兼容字段都完美挂载。
- B: 老 `synastry.py` 成了死物，打上 DEPRECATED 封条择日问斩。
- C: 前端目前用旧字段 `is_approved` 跑得很欢，无缝着陆。
- D/M: 工作树里塞满了 Round 22 和 23 的报告，必须立刻通过 Commit 和 Push 把它们护送到云上。
- E: 全网搜遍了，唯有 `VedAstro` 拥有能直接用于商用的 MIT Ashtakoot 打分字典，别无分店。
- F-G: 引擎出分必须附带 `VedAstro (MIT)` 版权标，并将 0/5 的合婚测试进度扔进大模型上下文里。
- H-I: 明确了火星煞（Kuja）的 4 级状态，和力量值（Shadbala）20 Rupa 封顶的防线。
- J-K: 给出了两个精简到极致的外包操作员破冰文档（JHora 与 AstroSage 截图填写法）。
- L: 开辟了 Playwright 的 12 条关键 E2E 断言战线。
- N-O: 定好了下一波 30 条副手分析单，以及 Codex 提取字典的大决战。

### 3. 旧结论纠偏表
| 报告项 | 之前轮次的旧结论 | 当前实际情况 |
|---|---|---|
| 推送上云 | 需 Push 上云 | ❌已过期，此前的两发（代码+Round 16-21）Commit 已在远端！但本轮和上轮的又积攒了一堆。 |
| 引擎切换 | `ashtakoot.py` 硬编码0，未接入 API | ❌已过期，API 已经 `_compute_synastry` 连上它了，只不过它自身还没常数。 |

### 4. 当前 P0/P1/P2 Bug 表
| 严重等级 | 文件/位置 | 现状与风险 | 最小修复建议 |
|---|---|---|---|
| **P0 (资产管理)** | Git 工作区 | Round 22 与 23 加起来 30 多份顶层架构决策和调研全在本地，系统一崩溃全白干。 | 执行 `git commit` 并极速 `git push origin codex/release-hygiene-ci`。 |
| **P1 (业务阻塞)** | `ashtakoot.py` | 它已经正式接客了，但因为没常数，还在发着伪造的 0 分糊弄人。 | 立刻新建 `ashtakoot_constants.py` 把 VedAstro 数据拿过来。 |

### 5. 可复用开源项目 Top 5 (MIT/Apache 等)
1. **VedAstro/VedAstro** (C#, MIT) - Ashtakoot 和谐矩阵的唯一指望。
2. **RaviKarrii/Marriage-Compatibility** (Java, MIT)
3. **panchanga** (Python, MIT)

### 6. 只能参考不能复制项目 Top 5 (AGPL/GPL/商业闭源)
1. **PyJHora** (AGPL-3.0) - 我们绝不沾碰它的代码。
2. **pyhora2** (MIT 壳装 AGPL) - 同上，坚决拉黑。
3. **AstroSage** (Web)
4. **JHora** (Desktop)

### 7. 必须等待人工外部工具事项
操作员必须领下 Report J 和 Report K 的包，在一台 Windows 上跑一次 JHora 给 Steve Jobs 盘截图！

### 8. 给 Codex 的 Top 25 下一步（精简）
1. 将 `docs/research/antigravity_round23*` 及 `round22*` 所有文件 `git add` 并封库！
2. 赶紧 `git push`！
3. 开辟 `ashtakoot_constants.py` 战场。
4. 去 GitHub 把 VedAstro 的 8 Kuta（特别是那恶心的 Yoni 14x14 和 Nadi 27 宿）全部手搓或脚本转成 Python Dict。
5. 在引擎接口挂上 MIT 的溯源 Provenance 标记。
6. 给 Validator 追加 `(0, 20.0)` 的 Shadbala Rupa 阈值封锁线。

> 下一步建议 Codex 优先：立刻将这积压了近 40 份的 Round 22 & 23 研究档案通过 Commit 和 Push 钉死在远端仓库，保护战果！随后的第一件业务大事，就是拿着我们精挑细选的、完全合法的 MIT 来源 `VedAstro`，去提取那套改变命运的 Ashtakoot 36分数组。同时，依然卑微地期盼人类执行者把那份 JHora 的 1/5 样本填好交上来。
