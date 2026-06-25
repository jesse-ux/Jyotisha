# Antigravity AI License 隔离墙复核 (Round 30)

## 不可触碰的毒代码

再怎么强调也不为过，以下三个本地库是 **绝对不许抄源码** 的：

1. `references/open_source_sources/PyJHora` 
   - **协议**: AGPL-3.0
   - **隔离级别**: 物理隔离。只许用来生成 Benchmark JSON 数据作比对。
2. `references/open_source_sources/jyotish` (kunjara)
   - **协议**: GPL-3.0
   - **隔离级别**: 仅供学术验证。
3. `references/open_source_sources/Maitreya`
   - **协议**: GPL
   - **隔离级别**: 禁止转译其 C++ 计算引擎。

**审计结果**：
当前我们的 `scripts/` 核心目录 **不存在** GPL 污染代码，所有占星推演（如 `jyotish_engine.py`）都是调用纯净版 `swisseph` 后从头自写的算法。

## 状态
`已成立`
