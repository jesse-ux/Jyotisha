# Antigravity AI Round 24 最终总报告 (2026-06-25)

## 核心回答
1. **当前印度占星 app 是否已经包含对标应用全部技能？** 否。我们离 JHora 等老牌软件还有很长路要走，尤其缺乏完整的 Panchang、极高阶分盘、KP系统和择吉引擎。
2. **哪些技能“本地能用”？** D1/D9/D10 落座、Vimshottari Dasha 时间树计算、Shadbala Rupa 数学计算、1000多种 Yoga 的模式匹配、基于假数据的 Ashtakoot API。
3. **哪些技能“能算但未证明准”？** Shadbala（能算出 5 Rupa，但不知道 JHora 算出来是不是也是 5 Rupa）、Dasha（时区和起算偏差缺乏截图对比）、Yoga 解读（缺乏海量大师背书）。
4. **哪些技能“UI 不可见”？** 除 D1,D9,D10 外的 13 种 Varga；Tajika 年盘；Chara Dasha。
5. **哪些技能“API 不可见”？** `varshaphala.py` (Tajika)。
6. **哪些技能“缺外部 oracle”？** 全都缺！目前 `valid_packets` 为 0，这意味着我们整个系统在生产环境下处于盲飞状态。
7. **哪些技能“解盘可信度不足”？** AI Prompt Pack 发挥过于自由，且未经过盲测打分。
8. **用户今天如何测试准确率？** 运行 `python3 scripts/local_accuracy_report.py --format markdown` 可快速浏览内部基准和 BPHS 防线。

## Top 100 ROI 任务分类
### 今天本地可做 (Top 25 节选)
- 把所有的 untracked reports 提交上云。
- 开辟 `ashtakoot_constants.py`。
- 将 VedAstro 的 36 分常量转为 Python Dict 填入。
- 把 `total_score` 算法接好。
- 在 `/api/synastry` 加入 MIT 溯源印记。
- 将 Trust Center 的双核 0/5 进度条拆开。
- 用 Playwright 加 12 道合盘 E2E 锁。
- 给 Validator 加 `< 20 Rupa` 和 `no_dosha` Enum 控制。

### 必须人工截图书写 (Top 10)
- Steve Jobs 的 Dasha 截图填入 `vimshottari_start_date`。
- Steve Jobs 的 Shadbala 截图填入 Rupa。
- AstroSage 某名人的合婚打分截图填入 8 Kuta。

### 必须联网/外部 API (Top 5)
- 无，我们拒绝收费 API，全靠内置开源。

### 必须等用户决策 (Top 5)
- README 里该怎么用中文描述准确率防线。
- Frontend 要不要用 Cypress 替代 Playwright。
- Ayanamsa 是否开放给用户随意切换（破坏一致性）。

### 已完成但需证明准确率 (Top 5)
- 经纬度/时区到本地平太阳时的推算。
- Vimshottari 的次级大运 (Antardasha) 切分点。
- Yoga F1 0.95 (需在盲测中证明其确实是有用的，而不仅是数学对的)。

### 看似完成只是表面 UI (Top 5)
- Ashtakavarga：只有数字没图表。
- 合盘：UI 有，API 有，但算分其实是瞎编的 0 分。
- Dasha：能展三层，但最底下一层对不对不知道。
- 导出 JSON：只是生抠数据，不是供人传阅的算命书。

## Round 25 第一优先级
**停止一切“算命花招”的代码堆砌，立刻执行双线突击**：
1. **Codex 线**：抢修 `ashtakoot_constants.py` 并抄录 VedAstro，把合盘这块空缺用真数字填满！同时把那 40 份 Untracked 报告 Commit！
2. **人类线**：去填那该死的 1/5 截图 JSON 破冰！
