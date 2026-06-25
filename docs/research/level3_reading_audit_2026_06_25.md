# Level 3 综合解盘外部输出审计（2026-06-25）

## 输入来源

- 附件：`/Users/wuyongnaren/.codex/attachments/83deacc4-729c-4405-b51f-57170e05f5de/pasted-text.txt`
- 盘主资料：`REDACTED_DATE 14:45`，中国河北REDACTED_PLACEREDACTED_PLACE矿区，女
- 本地复验命令使用秒级资料：`REDACTED_DATE 14:45:20`，`lat=36.466667`，`lon=114.2`，`tz=8`

本审计只核验“外部解盘文本里的可计算声明”，不评价主观心理叙事，也不把占星解释视为事件预测准确率。

## 可采纳内容

1. D1 基础落座大体正确：Leo Lagna、Moon Aquarius、Sun Aries、Mars Cancer、Mercury/Venus Pisces、Jupiter Virgo、Saturn Aquarius、Rahu Scorpio、Ketu Taurus。
2. D9 主要落座与本地引擎一致：D9 Lagna Cancer，Mars D1/D9 Cancer Vargottama，Mercury D9 Virgo，Venus D9 Libra。
3. Vimshottari 当前大运段与本地引擎一致：`Saturn MD / Ketu AD`，本地边界为 `2026-02-03` 至 `2027-03-14`。
4. Shadbala 强弱方向部分可用：当前本地 `Sun` 输出约 `9.7035 Rupa`，属于最强组；但外部文本没有给出完整分量表，不应当作为 Shadbala oracle。

## 不应采纳的计算声明

1. `Sun Ashwini Pada 1` 错误。当前本地计算为 `Sun Aries 3.5058° / Ashwini Pada 2`。按 3°20' 一个 Pada，3°30' 已进入 Pada 2。
2. `金星燃烧` 不成立。当前 Sun/Venus sidereal separation 约 `22.9612°`，且不在同一星座；即使按常见 Venus combust orb，也不应标为燃烧。
3. `均无严重逆行` 不完整。当前 `Jupiter` 与 `Venus` 均为 retrograde，Rahu/Ketu 也为逆行节点。
4. `Jupiter Virgo = 中性` 是本项目此前用户可见状态标签的真实漏判。行星尊严应按“行星对星座主星的态度”判断，Jupiter 对 Mercury 为敌，因此应输出 `入敌(Enemy Sign)`。
5. `Ashtakavarga 8宫 30+` 与本地 AV 不一致。当前 SAV：Pisces/8宫为 `19`，Taurus/10宫为 `32`。外部文本把“8宫有金水”混作 AV 高分，这是解释层混用，不是 Ashtakavarga 计算结果。
6. `True Node` 与报告中 Rahu/Ketu 度数互相不一致。True Node 本地为 Rahu Scorpio `19.5501°`、Ketu Taurus `19.5501°`；外部文本列出的约 `21°03'` 接近 Mean Node。

## 已修复的项目问题

### P1：用户可见 D1 尊严标签漏掉友敌状态

- 文件：`scripts/jyotish_engine.py`
- 根因：`compute_chart_data()` 输出 `status` 时只判断 Exalted / Debilitated / Own Sign，其他全部写成 `中性`；而 `_get_dignity_level()` 虽有友敌枚举，但关系方向使用的是“星座主星怎么看行星”，不适合用户可见的自然尊严标签。
- 修复：新增 `DIGNITY_LABELS` 与 `_get_planet_status_label()`，按“行星对星座主星的态度”输出 `入友(Friendly Sign)` / `入敌(Enemy Sign)`。
- 回归：`tests/test_cli_smoke.py::test_dignity_helper_uses_planet_attitude_to_sign_lord` 与 `test_chart_reports_friend_and_enemy_sign_dignity_for_user_case`。

### P1：前端 fallback 尊严标签也会漏掉友敌状态

- 文件：`jyotish-app/jyotish-engine.js`、`jyotish-app/analysis-deep.js`
- 根因：浏览器端 fallback 的 `computeChart()` 与 deep analysis 的 `planetStatus()` 只判断 Exalted / Debilitated / Own Sign。
- 修复：新增并复用 `getPlanetStatus()`，让前端 fallback 与后端用户可见标签一致。
- 回归：`tests/test_frontend_productization.py::test_frontend_fallback_chart_reports_friend_and_enemy_sign_dignity`。

## 产品待办

1. AI/综合解盘生成层应强制引用结构化 chart/ashtakavarga/shadbala/dasha 结果，不允许自由改写 Pada、retrograde、combust、SAV 分数。
2. 给解盘文本增加 claim audit：把生成文本中的可计算声明抽取出来，与 JSON 结果核对后标注 `verified / contradicted / unverified`。
3. Transit 叙事需要接入真实日期的过境计算与 Sade/Ashtama Shani 判定；外部文本的过境判断目前未被本地 full-reading 自动模块覆盖。
4. KP natal sublord 可作为后续增强项；当前项目已有 `kp`/`prashna`，但外部文本里的“未调用 KP”提醒说明普通综合解盘还需要更明确地展示哪些技法已调用、哪些没有。
