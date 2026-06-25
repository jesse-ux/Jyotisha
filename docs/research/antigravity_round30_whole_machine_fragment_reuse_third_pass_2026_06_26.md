# Antigravity AI 整机碎片第三轮复用排查 (Round 30)

## 刮骨搜刮本地资源

我翻遍了系统，找到了几个还能被榨干的“尸块”：

1. **`dashaflow/jaimini.py`**：这是个 MIT 库，里面有 `calculate_jaimini_karakas` 和 Arudha Padas 的算法。如果我们不想自己重写 Padas，可以直接把它的算法吸收到我们的 `jyotish_engine.py` 里。
2. **`tools/ppt_generator.py` (在 `jaimini-tropical` 里)**：虽然是生成 PPT 的，但里面包含了关于 Panchanga 五大分支极其优质的 **中文解释和规则文本**。这对我们写前端的 Tooltip（鼠标悬浮提示）极有价值。
3. **`local_accuracy_report.py` 本身**：目前它只能比对硬编码的名人（如 Steve Jobs）。其实可以稍微改改，让它支持 `--json-dir ./my_cases` 批量吃入外部手工截的盘，跑出 F1 score。

## 状态
`已成立`
