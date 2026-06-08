# Jyotish benchmark 第五轮：A10 / Arudha Pada 交叉验证

生成时间：2026-06-03

## 1. 本轮目的

- 验证当前 skill 的 A10 / Karma Pada / Rajya Pada 符号输出是否与独立公式和 PyJHora Arudha 实现一致。
- 样本仍为10个公开/虚构 smoke case，不包含用户个人资料。
- 本轮先验证 sign/source_sign/source_lord/exception_applied 等结构字段；A10 精确度数属于不同传统口径，暂不作为硬性匹配字段。

## 2. 总体结果

| Target | Total | Match | Mismatch | Match rate |
|---|---:|---:|---:|---:|
| independent_formula | 60 | 60 | 0 | 100.00% |
| pyjhora_bhava_arudha | 10 | 10 | 0 | 100.00% |

## 3. 逐样本 A10 Sign

| Sample | Local skill A10 | Independent formula | PyJHora A10 | Status |
|---|---|---|---|---|
| smoke_beijing_1990_noon | Virgo | Virgo | Virgo | match |
| smoke_cairo_1952_dawn | Capricorn | Capricorn | Capricorn | match |
| smoke_delhi_2000_midnight | Pisces | Pisces | Pisces | match |
| smoke_london_1970_evening | Virgo | Virgo | Virgo | match |
| smoke_losangeles_1995_night | Capricorn | Capricorn | Capricorn | match |
| smoke_newyork_1985_morning | Aquarius | Aquarius | Aquarius | match |
| smoke_paris_1989_noon | Scorpio | Scorpio | Scorpio | match |
| smoke_sao_paulo_2004_morning | Aries | Aries | Aries | match |
| smoke_sydney_1999_afternoon | Capricorn | Capricorn | Capricorn | match |
| smoke_tokyo_1964_noon | Gemini | Gemini | Gemini | match |

## 4. 仲裁结论

- 当前 skill 的 A10 sign 与独立 Jaimini Arudha formula 对齐。
- 当前 skill 的 A10 sign 与 PyJHora `bhava_arudhas_from_planet_positions()` 对齐。
- 因此 A10/Karma Pada 作为事业外显判断的计算入口，sign 层可暂定为通过；degree 层因为 PyJHora 同时提供 cusp-based longitude 版本，需单独定义传统口径后再纳入硬性 benchmark。