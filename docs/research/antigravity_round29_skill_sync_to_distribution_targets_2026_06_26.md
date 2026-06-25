# Antigravity AI 旧 Skill 与主仓同步差距 (Round 29)

## 碎片冲突盘点

我们的主仓 `yinduzhanxing/` 已经比外挂的 `~/.workbuddy/skills/jyotish-vedic-astrology/` 先进很多了。

1. **测试门禁 (`scripts/run_quality_gate.py`)**：主仓有严密的 `local_accuracy_report` 闭环，旧仓没有，如果 Agent 被旧仓误导，会去乱改 BPHS 核心常数。
2. **API 规范**：旧仓里的 `SKILL.md` 还停留在零散脚本调用的认知，没有更新统一的 RESTful API 路由表指南。
3. **开源合规界限**：主仓设立了严苛的 `quarantine` 和 MIT 可复用清单，旧仓甚至还存有 `PyJHora` 相关的直接复制代码（极度危险，违反 AGPL）。

## 执行对策
这不是去合并旧仓，而是 **必须用主仓的规范彻底覆盖旧仓**，特别是 `SKILL.md`、`technique_registry.json` 和 `strict-workflow-router.md`。

## 状态
`已成立`
