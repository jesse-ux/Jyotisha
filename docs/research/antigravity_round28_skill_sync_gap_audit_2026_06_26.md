# Antigravity AI Skill 本体同步缺口审计 (Round 28)

## 目录级冲突与陈旧状态

| 审查目标 | `jyotish-vedic-astrology` (外部全局 WorkBuddy Skill 库) | `yinduzhanxing` (当前主工作仓) | 同步建议 |
|---|---|---|---|
| **SKILL.md 本体** | 未包含最新的 Oracle Evidence Validator 和 Prompt Pack 护栏规则。 | 拥有最前沿的版本。 | **主仓向外同步**。旧 Skill 必须拉取新规范，否则别的模型会用旧思路做事。 |
| **technique_registry.json** | 仅记录了最开始几十个基础项。 | 已注册 68 个精细化技法。 | **完全覆盖**。用主仓替换全局。 |
| **strict-workflow-router.md** | 缺少 Accuracy Profile CI 的门禁跳线指示。 | 规定了明确的 profile 和 TDD 流程。 | **主仓向外同步**。 |
| **open_source_sources/ 夹** | 囤积了大量 GPL/AGPL 代码（如 PyJHora）的历史拷贝，存在法律隐患。 | 已被隔离或仅用作基准对标。 | **双向清理**。全局仓库必须标记 quarantine。 |

## TDD 同步脚本蓝图

我们不应该手工复制这些文件，因为极易漏配。需要一个类似于 `scripts/sync_skill_to_workbuddy.sh` 的脚本：

1. 检测当前工作树是否干净。
2. 将 `SKILL.md` 拷贝至 `~/.workbuddy/skills/jyotish-vedic-astrology/`。
3. 将 `references/technique_registry.json` 和 `references/strict-workflow-router.md` 拷贝覆盖。
4. 提醒用户将这个操作变成一个 CI hook（在发版时触发）。

## 状态
`已成立`
