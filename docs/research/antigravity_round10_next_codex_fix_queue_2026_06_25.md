# Antigravity AI 下一步给 Codex 的可执行修复建议 (Round 10)

## 下一步优先级执行队列

经过反复的防腐审计与外围盘点，我们已经探明了主仓的安全边界。现对 Codex 主线程下达最高优先级的动作指令卡，请严格按序执行：

1. **[P0] Git 同步与大扫除**：
   - 立即将 Round 9 和 Round 10 产生的所有 `docs/research/antigravity_round*.md` 以及附属的研究记录（如 `task_plan.md`）一并进行 `git add` 并推送至 GitHub 远端 `codex/release-hygiene-ci`。
   - **绝对红线**：禁止将 `output_report.txt` 和 `results_extracted.md` 加入追踪！务必将其写入 `.gitignore` 或直接从暂存区清理，保障用户的生辰资料与私密报告的物理级隔离。
2. **[P0] 补足前台透明度 (Trust Center 构建)**：
   - 在 `jyotish-app/index.html` 与 `main.js` 中新增一个显眼的“Dasha/Shadbala 校准状态”看板（或模态框）。它至少需要静态或动态告知普通用户：“由于高阶技法边界极其精微，我们当前正在与外网权威数据做校对（目前进度 0/5），在正式达标前，排出的起步时标请仅做参考。”
3. **[P1] 同步修补 AI 与 Skill 边界**：
   - 修改 `jyotish-app/ai-chat.js` 和 `SKILL.md`，在底座提示词中强力拉起一条警戒线：当遭遇查询精密大运断点时，无论大模型推演得多么笃定，都必须向用户复诵一遍“本部分引擎正处于外部证据严选与验证期，暂做相对强弱参考，不做命运的绝对推断”。
4. **[P1] 构建测试防衰退网**：
   - 在前端测试链条（如 `tests/test_frontend_productization.py`）中新增一个静态扫描断言：测试必须要搜寻到前端代码里存在诸如 `calibration status` 或对应的告警文案；若丢失，流水线必须将其作为阻断级错误抛出。
5. **[P1] 真值突围（持久战）**：
   - 既然“证据校验器”已经固若金汤，下一步就必须开始啃硬骨头：设法在断网/安全隔离的虚机或专用沙盒中运行 JHora 与 PyJHora，手工录入截屏和基准数值。在至少打满 3 份 Evidence Packet 并且让 Validator 亮起绿灯前，不停止该项采集工作。
