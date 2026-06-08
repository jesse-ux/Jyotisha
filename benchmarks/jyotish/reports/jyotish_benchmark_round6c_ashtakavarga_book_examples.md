# Jyotish benchmark 第六轮补充：Ashtakavarga 公开书例仲裁

生成时间：2026-06-03

## 1. 仲裁目的

- 使用 PyJHora `pvr_tests.py` 中嵌入的 PVR 书例 expected BAV/SAV 数组，比较当前 skill 与 PyJHora 哪个更贴近这些公开例题。
- 这不是复制 PyJHora 代码；只把其测试文件中的 expected arrays 当成外部书例 benchmark。
- 图表是公开/书例 chart，不包含用户个人资料。

## 2. 总体结果

| Engine | Kind | Total | Match | Mismatch | Match rate |
|---|---|---:|---:|---:|---:|
| local_skill | bav | 180 | 180 | 0 | 100.00% |
| local_skill | sav | 36 | 36 | 0 | 100.00% |
| pyjhora | bav | 180 | 180 | 0 | 100.00% |
| pyjhora | sav | 36 | 36 | 0 | 100.00% |

## 3. 逐书例摘要

| Example | Local BAV | PyJHora BAV | Local SAV | PyJHora SAV |
|---|---:|---:|---:|---:|
| pvr_chart_6 | 96/96 | 96/96 | 12/12 | 12/12 |
| pvr_chart_7 | 84/84 | 84/84 | 12/12 | 12/12 |
| pvr_chart_12_sav_only | 0/0 | 0/0 | 12/12 | 12/12 |

## 4. 仲裁结论

- 当前 skill 与 PyJHora 对 PVR 公开书例均达到 100% 匹配。
- 这说明 v2.1 Moon/Venus 贡献表项校准已修复第六轮初始差异；Ashtakavarga BAV/SAV 可列为通过。