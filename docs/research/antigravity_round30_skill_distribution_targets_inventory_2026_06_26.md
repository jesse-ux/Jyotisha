# Antigravity AI Skill 分发目标实地盘点 (Round 30)

## 技能不是孤岛

我们虽然在 `~/Documents/印度占星` 里修好了所有 BUG，但如果没有向外分发，用户在其他 IDE 会话里呼出 Agent 时，Agent 依然是个“只会基本盘的瞎子”。

| 目标分发位置 | 作用 | 盘点现状 |
|---|---|---|
| `~/.workbuddy/skills/jyotish-vedic-astrology/` | 本机全局 Agent 技能底座 | **过时**。缺少最近五轮大更的 `technique_registry` 和 `SKILL.md` 护栏。 |
| GitHub Repository | 极客用户与开源社区 | `codex/release-hygiene-ci` 分支很新，但 `main` 分支陈旧。 |
| Npm / PyPi 包 | 供第三方开发者调用 | 未建包。当前只能源码运行。 |
| Docker Hub | 提供给小白一键跑服务 | 无 `Dockerfile`，无镜像发布。 |
| PWA 静态站点 | 用户扫码即用 | `jyotish-app/dist` 能够 build，但尚未部署到 Vercel/Netlify。 |

## TDD 要求
写一个 `scripts/distribute_skill.sh`，一键执行上述 WorkBuddy 目录的文件覆盖。

## 状态
`部分成立`
