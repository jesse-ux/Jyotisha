# Jyotish benchmark 第六轮：Ashtakavarga BAV/SAV 交叉验证

生成时间：2026-06-03

## 1. 本轮目的

- 验证当前 skill 的 Ashtakavarga BAV/SAV 是否与 PyJHora `get_ashtaka_varga()` 对齐。
- 同时检查内部不变量：7行星 SAV 总分=337；含 Lagna full SAV 总分=386；各行星 BAV 固定总分正确。
- 样本仍为10个公开/虚构 smoke case，不包含用户个人资料。

## 2. 总体结果

| Target | Total | Match | Mismatch | Match rate |
|---|---:|---:|---:|---:|
| pyjhora_sav | 120 | 120 | 0 | 100.00% |
| pyjhora_bav | 960 | 960 | 0 | 100.00% |
| invariants | 30 | 30 | 0 | 100.00% |

## 3. 逐样本摘要

| Sample | SAV match | BAV match | SAV total | Full SAV | Strongest signs | Weakest signs |
|---|---:|---:|---:|---:|---|---|
| smoke_beijing_1990_noon | 12/12 | 96/96 | 337 | 386 | Sagittarius, Libra, Taurus | Capricorn, Cancer, Aquarius |
| smoke_newyork_1985_morning | 12/12 | 96/96 | 337 | 386 | Pisces, Gemini, Aries | Cancer, Virgo, Aquarius |
| smoke_london_1970_evening | 12/12 | 96/96 | 337 | 386 | Capricorn, Cancer, Aquarius | Virgo, Aries, Pisces |
| smoke_delhi_2000_midnight | 12/12 | 96/96 | 337 | 386 | Virgo, Libra, Cancer | Taurus, Gemini, Capricorn |
| smoke_sydney_1999_afternoon | 12/12 | 96/96 | 337 | 386 | Gemini, Capricorn, Aquarius | Sagittarius, Pisces, Cancer |
| smoke_tokyo_1964_noon | 12/12 | 96/96 | 337 | 386 | Taurus, Virgo, Aries | Pisces, Leo, Scorpio |
| smoke_cairo_1952_dawn | 12/12 | 96/96 | 337 | 386 | Taurus, Sagittarius, Aries | Aquarius, Pisces, Gemini |
| smoke_paris_1989_noon | 12/12 | 96/96 | 337 | 386 | Leo, Libra, Taurus | Virgo, Gemini, Scorpio |
| smoke_losangeles_1995_night | 12/12 | 96/96 | 337 | 386 | Virgo, Taurus, Libra | Leo, Scorpio, Gemini |
| smoke_sao_paulo_2004_morning | 12/12 | 96/96 | 337 | 386 | Sagittarius, Aries, Gemini | Taurus, Virgo, Libra |

## 4. 仲裁结论

- 若 `pyjhora_sav` 与 `pyjhora_bav` 均为 100%，则 Ashtakavarga BAV/SAV 计算层可暂定通过。
- Shodhya Pinda 不纳入本轮硬性通过；PyJHora 源码示例本身说明个别书例存在不一致，适合单独做弱口径验证。