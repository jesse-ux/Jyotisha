# Jyotish benchmark 第七轮：Chara Dasha / Jaimini 时间线对标

生成时间：2026-06-03

## 1. 本轮目的

- 验证当前 skill `scripts/jaimini.py` 的 Chara Dasha 是否可作为正式计算模块使用。
- 对标对象：PyJHora `raasi/chara.py` 的 KN Rao method（PyJHora 默认 `CHARA_TYPE_DEFAULT = KN_RAO`）。
- 样本仍为10个公开/虚构 smoke case，不包含用户个人资料。

## 2. 总体结果

| Field group | Total | Match | Mismatch | Match rate |
|---|---:|---:|---:|---:|
| sequence_sign | 120 | 50 | 70 | 41.67% |
| duration_years | 120 | 8 | 112 | 6.67% |
| all | 240 | 58 | 182 | 24.17% |

## 3. 逐样本摘要

| Sample | Sign match | Duration match | Local first 3 | PyJHora first 3 |
|---|---:|---:|---|---|
| smoke_beijing_1990_noon | 2/12 | 0/12 | Pisces(12), Aquarius(11), Capricorn(10) | Pisces(9), Aries(7), Taurus(8) |
| smoke_newyork_1985_morning | 12/12 | 0/12 | Leo(12), Virgo(12), Libra(11) | Leo(2), Virgo(2), Libra(7) |
| smoke_london_1970_evening | 2/12 | 1/12 | Virgo(12), Leo(11), Cancer(12) | Virgo(5), Libra(6), Scorpio(9) |
| smoke_delhi_2000_midnight | 2/12 | 0/12 | Virgo(12), Leo(12), Cancer(12) | Virgo(9), Libra(3), Scorpio(2) |
| smoke_sydney_1999_afternoon | 12/12 | 1/12 | Capricorn(12), Sagittarius(12), Scorpio(11) | Capricorn(8), Sagittarius(4), Scorpio(2) |
| smoke_tokyo_1964_noon | 2/12 | 3/12 | Sagittarius(12), Capricorn(12), Aquarius(11) | Sagittarius(5), Scorpio(2), Libra(10) |
| smoke_cairo_1952_dawn | 12/12 | 0/12 | Cancer(9), Gemini(12), Taurus(12) | Cancer(12), Gemini(2), Taurus(2) |
| smoke_paris_1989_noon | 2/12 | 1/12 | Sagittarius(10), Capricorn(12), Aquarius(12) | Sagittarius(6), Scorpio(11), Libra(2) |
| smoke_losangeles_1995_night | 2/12 | 1/12 | Sagittarius(12), Capricorn(12), Aquarius(11) | Sagittarius(11), Scorpio(7), Libra(6) |
| smoke_sao_paulo_2004_morning | 2/12 | 1/12 | Pisces(12), Aquarius(10), Capricorn(12) | Pisces(7), Aries(12), Taurus(11) |

## 4. 仲裁结论

- 当前 skill 的 Chara Dasha 与 PyJHora KN Rao method 存在明显差异。
- 根因从源码可见：当前 `calc_chara_dasha()` 仍是简化实现（上升顺/逆 + `12 - sign planet count`），并非 KN Rao / PVN Rao / Iranganti 的完整传统算法。
- 决策：Chara Dasha 不应标记为 `covered` 的强计算模块；在可信度矩阵中应降级为 `partial-code`，除非后续直接实装 KN Rao/PVN Rao method 并回归通过。
- 加速策略：可把 PyJHora KN Rao method 作为外部 oracle，重写本地 Chara Dasha；或者在 skill 中明确声明 Jaimini Chara Dasha 暂不可用于高置信度应期。