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
| Chara Dasha / Jaimini | Yes | Partial | Yes | Partial | `partial` | Chara Karaka/Karakamsha are usable, but Chara Dasha timing is a simplified implementation. Round 7 benchmark vs PyJHora KN Rao method matched only 58/240 fields (24.17%); do not use as high-confidence timing until KN Rao/PVN Rao/Iranganti method is implemented and revalidated. |
| Karakamsha / AK | Yes | Yes | Yes | Yes | `covered` | `full-reading` uses AK, not DK. |
| Argala | Yes | Yes | Yes | Yes | `covered` | `argala` module and strict routes. |
| Shadbala | Yes | Partial | Yes | Yes | `partial` | Internal invariants passed 1200/1200 in Round 9, and `shadbala` matches `full-reading`; however current implementation still contains simplified Nathonnata Bala, Saptavargaja approximations, Chesta speed buckets and simplified Drik weights. Use as internally consistent strength reference, not externally calibrated Parashara absolute Shadbala. |
| Ashtakavarga | Yes | Yes | Yes | Yes | `covered` | `ashtakavarga` module and validation. |
| Avastha | Yes | Yes | Yes | Yes | `covered` | `scripts/avastha_calculator.py` integrated in `full-reading`. |
| Vargottama | Yes | Yes | Yes | Yes | `covered` | App existed before; v6.0.2 adds `full-reading.modules.vargottama`. |
| AL / Arudha Lagna | Yes | Yes | Yes | Yes | `covered` | `special_lagnas.py` + `full-reading`. |
| UL / Upapada Lagna | Yes | Yes | Yes | Yes | `covered` | `special_lagnas.py` + `full-reading`. |
| A10 / Karma Pada / Rajya Pada | Yes | Yes | Yes | Yes | `covered` | v6.0.2 adds generic Arudha Pada and `calculate_a10()`. |
| Pushkara Navamsa / Bhaga | Yes | Yes | Yes | Yes | `covered` | v6.0.2 adds automatic D1 Pushkara flags in `full-reading`. |
| Dasha Sandhi | Yes | Yes | Yes | Yes | `covered` | v6.0.2 adds Mahadasha/Antardasha boundary windows around reference date. |
| Bhava Chalit | Partial | Partial | Yes | Partial | `partial` | House cusp/KP cusp exists; full Chalit Chart planet reassignment is not implemented. |
| Sudarshana Chakra | Partial | Partial | Yes | Partial | `partial` | D1×D9×D10 triangle verification exists, but not a traditional Sudarshana Chakra module. |
| KP / Sub-lord | Yes | Yes | Yes | Yes | `covered` | KP references and sub-lord calculations exist. |
| Tajika / Varshaphala | Yes | Yes | Yes | Yes | `covered` | `tajika` and `full-reading`. |
| Double Transit | Yes | Yes | Yes | Yes | `covered` | `double-transit-pac`, transit multi-reference. |

## Practical rule for future readings

When producing a Technique Audit Table:

1. Do not mark a technique as missing if any layer exists.
2. Use `partial` for Chara Dasha/Jaimini timing, Shadbala, Bhava Chalit, and Sudarshana until full traditional modules are added or externally benchmark-validated.
3. For Jaimini output, separate reliable Karaka/Karakamsha indicators from partial Chara Dasha timing; cap timing confidence if Chara Dasha is used.
4. For Shadbala output, state that current scores are internally consistent but not yet externally calibrated to a full Parashara/JHora-style absolute Shadbala table.
5. Use `covered` for A10, Vargottama, Pushkara, Avastha, and Dasha Sandhi from v6.0.2 onward, but still state whether the current run actually called `full-reading`.
6. If a user provides only PDF text without exact degrees, Pushkara/Vargottama/A10 may degrade to `manual` or `unavailable` because the data layer is insufficient.
