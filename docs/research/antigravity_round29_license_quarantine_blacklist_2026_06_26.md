# Antigravity AI License Quarantine 黑名单 (Round 29)

## 坚决不可碰触的红线区域

为了保证本项目未来能直接变现、出售、SaaS 化而免受 GPL 传染病起诉，以下项目必须被打上 `benchmark_only` 标签：

1. **PyJHora (AGPL)**：只许给它发输入并比对它的输出。绝对禁止抄袭其内部的 Dasha 计算函数和 Yoga 解析函数。
2. **Maitreya (GPL)**：只做外部参照比对，绝不能抄其 C++ 核心转换为 Python。
3. **kunjara/jyotish (GPL)**：不可看其内部实现。
4. **所有 AstroSage/Drik 的前端 JS**：这是闭源商用财产，不可破解其源码，只许抓取它的最终页面渲染结果做黑盒对比。

## TDD 测试断言
必须在 CI 中加一条脚本：`grep -ri "pyjhora" scripts/`，如果在核心计算模块出现这个词，直接阻断提交（证明有抄袭嫌疑或过度耦合）。

## 状态
`已成立`
