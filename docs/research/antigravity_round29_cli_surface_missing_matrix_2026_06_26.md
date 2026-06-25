# Antigravity AI CLI 未暴露能力总表 (Round 29)

## 极客可用性分析

在服务端和 CI 场景，CLI 的好用程度决定了排障效率。目前 `jyotish_engine.py` 只能吐 JSON。

1. **表格模式 (`--table`)**：
   使用 `tabulate` 库在终端直接输出对齐的星位表和 Shadbala 表，避免人类肉眼解析 JSON。
2. **彩色打印**：
   引入 `colorama`，吉星用绿色，凶星（罗睺计都土星火星）用红色，耀升加亮。
3. **合婚对比 (`--match <file1> <file2>`)**：
   接受两个 JSON 生辰文件，在命令行直接输出 8 项对比分数。
4. **择吉查询 (`scripts/muhurta.py --month 2026-06 --lat 39 --lon 116`)**：
   输出该月所有符合条件的吉日。
5. **版本与协议查询 (`--version`, `--license`)**：
   CLI 需要自我申明使用 MIT 协议和底层 swisseph 的存在。

## 状态
`部分成立`
