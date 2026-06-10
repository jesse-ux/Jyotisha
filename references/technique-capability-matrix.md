# Technique Capability Matrix — Jyotish Skill v6.0.11

> Purpose: prevent vague statements like “covered” or “missing”. Each technique is classified by four layers: knowledge, computation, orchestration, and output.

## Status vocabulary

| Status | Meaning |
|---|---|
| `covered` | Knowledge + computation + workflow + output are available. |
| `partial` | Some layers exist but not a complete traditional implementation. |
| `knowledge-only` | Reference documentation exists, but no executable calculation. |
| `workflow-only` | Checklist/router mentions the technique, but no calculation module. |
| `not-integrated` | Code exists somewhere, but full-reading/normal workflow does not expose it. |
| `missing` | No meaningful local coverage found. |

## Capability matrix

| Technique | Knowledge layer | Computation layer | Workflow/orchestration | Output layer | Final status | Notes |
|---|---:|---:|---:|---:|---|---|
| D1 / Rashi | Yes | Yes | Yes | Yes | `covered` | Core `chart` and `full-reading`. |
| D9 / Navamsa | Yes | Yes | Yes | Yes | `covered` | `varga-full`, D9 expanded dignity. |
| D10 / Dasamsa | Yes | Yes | Yes | Yes | `covered` | `varga-full`, strict career route requires it. |
| Vimshottari Dasha | Yes | Yes | Yes | Yes | `covered` | `dasha` and `full-reading`. |
| Chara Dasha / Jaimini | Yes | Yes | Yes | Yes | `partial` | v6.1.10: 修复birth balance + Pratyantar Dasha 3层递归（MD→AD→PD），大运使用行星计数法。但未与KN Rao/PVN Rao完全对标，仍保留partial。v6.1.11 新增 Jaimini 静态层：A1-A12/UL、Graha Pada、Hora/Ghatika/Varnada 等 Special Lagnas 输出；这些静态指标可用，Chara Dasha timing 仍降权。 |
| Karakamsha / AK | Yes | Yes | Yes | Yes | `covered` | `full-reading` uses AK, not DK. |
| Jaimini Arudha A1-A12 / UL | Yes | Yes | Yes | Yes | `covered` | v6.1.11: `scripts/jaimini.py` 暴露 `calc_arudha_padas()`，`jaimini --mode all/arudha` 与 `full-reading.modules.jaimini.arudha_padas` 输出 A1-A12，其中 A12 作为 UL/Upapada。 |
| Graha Pada | Yes | Yes | Yes | Yes | `covered` | v6.1.11: `calc_graha_padas()` 已接入 `jaimini` 子命令与 `full-reading.modules.jaimini.graha_padas`；用于行星镜像/显化层分析。 |
| Jaimini Special Lagnas | Yes | Yes | Yes | Yes | `partial` | v6.1.11: `calc_special_lagnas()` 输出 Hora/Ghatika/Varnada Lagna，当前为简化午夜 ghati 近似，非日出校正版，标注 auxiliary_partial。 |
| Argala | Yes | Yes | Yes | Yes | `covered` | v6.1.11: `argala.py` 已升级为 Argala + Virodhargala + Rajayoga classification，覆盖 2/4/11 主 Argala、12/10/3 阻挡、5/9 次级 Argala 与第3宫凶星特殊 Argala。 |
| Shadbala | Yes | Yes | Yes | Yes | `covered` | v6.1.10: 完整修复。Nathonnata比例计算(0-60渐变)、Chesta Sun速度五档、Ishta/Kashta Phala、Saptavargaja调用varga.py实际分盘、Naisargika对标PyJHora(60-8.57递减)。JHora基准测试全部通过。 |
| Ashtakavarga | Yes | Yes | Yes | Yes | `covered` | `ashtakavarga` module and validation. |
| Avastha | Yes | Yes | Yes | Yes | `covered` | `scripts/avastha_calculator.py` integrated in `full-reading`. |
| Vargottama | Yes | Yes | Yes | Yes | `covered` | App existed before; v6.0.2 adds `full-reading.modules.vargottama`. |
| AL / Arudha Lagna | Yes | Yes | Yes | Yes | `covered` | `special_lagnas.py` + `full-reading`. |
| UL / Upapada Lagna | Yes | Yes | Yes | Yes | `covered` | `special_lagnas.py` + `full-reading`. |
| A10 / Karma Pada / Rajya Pada | Yes | Yes | Yes | Yes | `covered` | v6.0.2 adds generic Arudha Pada and `calculate_a10()`. |
| Pushkara Navamsa / Bhaga | Yes | Yes | Yes | Yes | `covered` | v6.0.2 adds automatic D1 Pushkara flags in `full-reading`. |
| Dasha Sandhi | Yes | Yes | Yes | Yes | `covered` | v6.0.2 adds Mahadasha/Antardasha boundary windows around reference date. |
| Bhava Chalit | Yes | Yes | Yes | Yes | `covered` | v6.1.10: `scripts/bhava_chalit.py` 完整实现（等宫制从Lagna中点划分，跨宫检测，Cusp/Madhya计算）。代码基于dashaflow(MIT)。 |
| Sudarshana Chakra | Yes | Yes | Yes | Yes | `covered` | v6.1.10: `scripts/sudarshana_chakra.py` 完整实现（三轮盘三环汇聚 + D1×D9×D10三角分析 + 12年周期大运）。参考PyJHora思路自行编码。 |
| KP / Sub-lord | Yes | Yes | Yes | Yes | `covered` | KP references and sub-lord calculations exist. |
| Synastry / Ashta Koota + Additional Kutas | Yes | Yes | Yes | Yes | `covered` | v6.1.11: `synastry.py` 在 Ashta Koota 36分、Mangal Dosha、Papasamya 基础上新增 Mahendra、Stree Deergha、Vedha、Rajju、BadConstellations 与例外减弱规则，输出 `additional_kutas`。 |
| Tajika / Varshaphala | Yes | Yes | Yes | Yes | `covered` | `tajika` and `full-reading`. |
| Double Transit | Yes | Yes | Yes | Yes | `covered` | `double-transit-pac`, transit multi-reference. |

## Practical rule for future readings

When producing a Technique Audit Table:

1. Do not mark a technique as missing if any layer exists.
2. Use `partial` for Chara Dasha/Jaimini timing and Special Lagnas until full KN Rao/PVN Rao/Iranganti timing and sunrise-corrected Lagna methods are externally benchmark-validated.
3. For Jaimini output, separate reliable static indicators (Karaka/Karakamsha, A1-A12/UL, Graha Pada, Argala/Virodhargala) from partial Chara Dasha timing; cap timing confidence if Chara Dasha is used.
4. For Shadbala output, state whether the current run used the internally validated components or an externally calibrated JHora-style benchmark table.
5. Use `covered` for A10, Vargottama, Pushkara, Avastha, and Dasha Sandhi from v6.0.2 onward, but still state whether the current run actually called `full-reading`.
6. If a user provides only PDF text without exact degrees, Pushkara/Vargottama/A10 may degrade to `manual` or `unavailable` because the data layer is insufficient.
