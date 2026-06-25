# Antigravity AI 开源社区贡献指南 (Round 28)

## 如果我们要冲全球第一
光靠 Codex 是不够的，必须吸引印度当地的占星程序员贡献代码。他们懂算法但往往代码写得很烂。

## CONTRIBUTING.md 纲要
1. **测试先行**：任何人提交一个新的算命逻辑（如新的 Dasha），必须附带一个能和 JHora 输出对齐的 JSON Evidence，并让 `run_quality_gate.py` 通过。
2. **禁止 GPL 污染**：贡献者绝不能抄袭其他带毒库的代码，我们强制要求提供算法公式原出处。
3. **前后分离**：不要提交又改算法又改 DOM 的混合型 PR。
4. 提供一个 `/scripts/scaffold_new_technique.py` 的脚手架生成器。

## 状态
`未成立`
