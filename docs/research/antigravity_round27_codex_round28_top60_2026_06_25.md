# Antigravity AI Codex Round 28 立即实现 Top 60 (Round 27)

| 优先级 | 任务名 | 目标文件 / 模块 | 动作 | 人工 |
|---|---|---|---|---|
| **1** | R27 归档 | `git CLI` | 暂存并提交这几十份 R27 报告。 | 否 |
| **2** | CI 门禁加入 | `.github/workflows/accuracy.yml` | 按 R27 规格创建该 CI，并配置 Python/pytest。 | 否 |
| **3** | Shadbala Rupa 上限 | `oracle_evidence_validator.py` | 拦截 Rupa > 20 的假数据。 | 否 |
| **4** | Shadbala 总分容差 | `oracle_evidence_validator.py` | 验证 `abs(sum - total) < 0.05`。 | 否 |
| **5** | Kuja Enum 验证 | `oracle_evidence_validator.py` | 加入 `['high_dosha', 'neutralized', ...]` 校验。 | 否 |
| **6** | API Kuja 迁移 | `jyotish_api_server.py`, `ashtakoot.py`| 将火星煞返回的 bool 转为 Enum 字符串。 | 否 |
| **7** | Ashtakoot 常量拆分 | `ashtakoot_constants.py` | 新建文件并注上 MIT 来源，准备移表。 | 否 |
| **8** | Ashtakoot 矩阵植入 | `ashtakoot_constants.py` | 手把手抄入 Varna、Yoni 等敌对矩阵字典。 | 否 |
| **9** | Ashtakoot 换核 | `ashtakoot.py` | 用常量表替换掉原来的 mock 返回值。 | 否 |
| **10** | Prompt 护栏断言 | `tests/test_prompt_security.py` | 断言生成的文案必含“禁止铁口直断”及医疗免责。 | 否 |
| **11** | Prompt 护栏植入 | `prompt_generator.py` | 动态拼接安全指令。 | 否 |
| **12** | 统一 JSON 抛错 | `jyotish_api_server.py` | 包裹 500 异常，拒绝吐出 HTML traceback。 | 否 |
| **13** | 暴露 Tajika 年运 | `jyotish_api_server.py` | 增加 `/api/tajika` 路由与验证。 | 否 |
| **14** | Varga 前端下拉框 | `jyotish-app/main.js` | 增加下拉菜单复用 SVG renderer，解锁 D7-D60。 | 否 |
| **15** | Chara Dasha 前端 | `jyotish-app/main.js` | 给大运树加个 Vim/Chara 的切换 Tab。 | 否 |
| **16** | Panchang 月历表 | `jyotish-app/main.js` | 把 `/api/panchanga_range` 画成基础的 HTML 表格。 | 否 |
| **17** | CLI Table 模式 | `jyotish_engine.py` | 在 main 块加 `--table` 参数。 | 否 |
| **18** | Chara CLI 补全 | `chara_dasha.py` | 加 `argparse`，不再裸奔报错。 | 否 |
| **19** | Varshaphala CLI | `varshaphala.py` | 加 `argparse`。 | 否 |
| **20** | 稳定 JSON Diff | `validate_logic_v2.py` | 生成报告时加 `sort_keys=True` 稳住顺序。 | 否 |
| 21-60 | (按需顺延) | - | 等前 20 消化完再推。 | - |
