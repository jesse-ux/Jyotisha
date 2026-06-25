# Antigravity AI 云端同步白名单计划 (Round 29)

## 全局 WorkBuddy 覆盖准则

我们要把 `yinduzhanxing/` 主仓里的智慧辐射到用户其他项目中。
**必须用主仓的文件去覆盖 `~/.workbuddy/skills/jyotish-vedic-astrology/`，绝不能反过来。**

### 同步白名单
1. `SKILL.md`：核心灵魂，包含我们写的 Prompt 护栏和 `run_quality_gate.py` 命令。
2. `references/technique_registry.json`：68 个技法的确切状态，旧仓里的太老了。
3. `references/strict-workflow-router.md`：我们刚设计的 TDD 断言跳线图。
4. `docs/research/` 的归档精华（可压缩后存放）：让新开的 Agent 也能学到前几轮的心血。

### 禁止同步黑名单 (Quarantine)
1. 任何 `*.py` 源码：Skill 本身不该携带几万行代码，而是应该以 Tool 的形式存在。
2. GPL / PyJHora 等带毒代码段。

## 状态
`已成立`
