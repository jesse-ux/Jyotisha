# Antigravity AI Codex Round 27 立即实现 Top 40 (Round 26)

Codex 必须立刻执行以下清单，否则副手的报告就会沦为空谈：

| 优先级 | 任务描述 | 目标文件 | 验收标准 / 测试 | 是否需人工 |
|---|---|---|---|---|
| 1 | 归档 R25/R26 | 根目录终端 | `git add docs/research/` & `git commit` | 否 |
| 2 | Push 上云 | 根目录终端 | 用 HTTPS push 成功。 | 是 (输Token) |
| 3 | CI 门禁加入 | `.github/workflows/accuracy.yml` | 创建并触发 Action。 | 否 |
| 4 | Shadbala Validator | `oracle_evidence_validator.py` | `< 20.0` 及 sum 容差 `< 0.05`。 | 否 |
| 5 | Kuja Enum Validator | `oracle_evidence_validator.py` | 拦截非 Enum 的火星煞字段。 | 否 |
| 6 | 替换 API 返回的 Kuja | `jyotish_api_server.py` | 返回 `"high_dosha"` 而不是 `true`。 | 否 |
| 7 | Ashtakoot 词典建立 | `ashtakoot_constants.py` | 把 VedAstro 的 8 个矩阵复制进去。 | 否 |
| 8 | Ashtakoot 换心手术 | `ashtakoot.py` | 用新矩阵跑通原有测试用例。 | 否 |
| 9 | Panchang UI | `jyotish-app/main.js` | 把 `/api/panchanga_range` 画成日历 `<table>`。 | 否 |
| 10 | Prompt 安全护栏 | `prompt_generator.py` (或相关) | 硬编码免责声明。 | 否 |
| 11 | Prompt TDD 测试 | `tests/test_prompt_security.py` | 验证生成的长文本里必定含免责声明。 | 否 |
| 12 | 暴露 Tajika API | `jyotish_api_server.py` | 增加 `/api/tajika` 路由。 | 否 |
| 13 | 增加 Chara Dasha 前端 | `jyotish-app/main.js` | 在运势树加个新 Tab 显示 Jaimini 运。 | 否 |
| 14 | 增加 D7/D60 前端 | `jyotish-app/main.js` | 加个下拉框复用 SVG renderer。 | 否 |
| 15 | 修复 Chara CLI | `scripts/chara_dasha.py` | 改用 `argparse`。 | 否 |
| 16 | 修复 Varshaphala CLI | `scripts/varshaphala.py` | 改用 `argparse`。 | 否 |
| 17 | README 免责 | `README.md` | 写入 R26 的白话安全说明。 | 否 |
| 18 | License 补充 | `NOTICE.md` | 列出 VedAstro, flatlib 等 MIT 致谢。 | 否 |
| 19 | 解决端口占用报错 | `jyotish_api_server.py` | 加上 `try/except OSError`。 | 否 |
| 20 | JSON 格式化输出 | `jyotish_engine.py` | 在命令行加 `indent=2`。 | 否 |
| 21-40 | 略 | 略 | 优先把前 20 干完。 | 否 |
