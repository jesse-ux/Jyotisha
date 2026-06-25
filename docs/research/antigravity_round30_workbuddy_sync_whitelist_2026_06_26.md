# Antigravity AI WorkBuddy 覆盖白名单 (Round 30)

## 精确到文件的推送指令

我们必须写一个 bash 脚本，严格按照以下命令，把本仓的心血转移到用户的全局 WorkBuddy 库中，不能有丝毫偏差。

### 执行令集

```bash
# 1. 确保目标存在
TARGET_DIR=~/.workbuddy/skills/jyotish-vedic-astrology
mkdir -p "$TARGET_DIR/references"

# 2. 同步主控脑图
cp ./SKILL.md "$TARGET_DIR/"
cp ./references/strict-workflow-router.md "$TARGET_DIR/references/"
cp ./references/technique_registry.json "$TARGET_DIR/references/"

# 3. 危险物清理 (在旧仓中删掉过度耦合的代码参照)
rm -rf "$TARGET_DIR/references/open_source_sources/PyJHora"

# 4. 同步研究文档 (让其他 Agent 拥有前世记忆)
# 先清空目标地的旧研究，防止文件名混乱
rm -rf "$TARGET_DIR/docs/research"
mkdir -p "$TARGET_DIR/docs/research"
cp ./docs/research/antigravity_round*.md "$TARGET_DIR/docs/research/"
```

这条脚本由下一轮的 Codex 直接封装为 `scripts/sync_to_workbuddy.sh` 并执行。

## 状态
`已成立`
