# Antigravity AI 云端同步白名单二次审计 (Round 30)

## 避免脏数据上云的红线

我们的主仓越来越强，但如果我们把带有调试信息、GPL 毒代码或者测试缓存的文件推给 WorkBuddy 全局库，就会污染所有 Agent 的认知。

### 允许同步上云的白名单 (Whitelist)
1. **指令与规范层**：
   - `SKILL.md` (Agent 唯一的入口大纲)
   - `references/strict-workflow-router.md` (TDD 工作流，防 Agent 瞎搞)
   - `references/technique_registry.json` (向世界宣告我们能算什么)
   - `references/oracle/` 目录下的 **空模板 JSON**。
2. **研究报告精华**：
   - `docs/research/` 中以 `antigravity_round*` 开头的所有 markdown。它们是对占星学数字化的最高结晶。

### 绝对禁止同步的黑名单 (Blacklist)
1. **源码**：不要把 `scripts/*.py` 同步到 Skill 库！Skill 是告诉大模型怎么使用 Tool，而不是把 Tool 的源码塞给大模型！
2. **带毒第三方库**：`references/open_source_sources/PyJHora` 等 AGPL 产物。
3. **运行时垃圾**：`__pycache__`, `node_modules`, `jyotish-app/dist`, `*.log`, `.pytest_cache`。

## 状态
`已成立`
