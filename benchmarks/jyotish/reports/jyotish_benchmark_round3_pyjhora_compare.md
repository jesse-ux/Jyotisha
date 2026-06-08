# Jyotish benchmark 第三轮：PyJHora 对比报告

生成时间：2026-06-03

## 1. 本轮范围

- 外部引擎：PyJHora 4.8.6。
- 用途：第二个独立 Jyotish 开源项目对标，重点验证 D1、D9、D10，并初探 Vimshottari。
- 样本：10个公开/虚构 smoke case，不包含用户个人资料。
- 口径：强制 Lahiri；PyJHora 默认 TRUE_PUSHYA，因此本轮显式切换到 LAHIRI。
- 兼容处理：PyJHora 4.8.6 与本机 pyswisseph API 存在关键字参数/常量兼容问题，本脚本只在 benchmark 进程内 monkeypatch，不改 PyJHora 源码，不把 AGPL 代码并入 skill。

## 2. 总体结果

- 字段总数：840
- 匹配：764
- 不匹配：68
- 边界敏感：8
- 总严格匹配率：90.95%
- 非 Dasha 字段严格匹配率：90.26%
- 非 Dasha 字段边界归因后可接受率：91.28%

## 3. 分区统计

| Section | Total | Match | Mismatch | Boundary sensitive | Not comparable |
|---|---:|---:|---:|---:|---:|
| D10 | 200 | 174 | 22 | 4 | 0 |
| D9 | 200 | 176 | 20 | 4 | 0 |
| ascendant | 20 | 20 | 0 | 0 | 0 |
| dasha | 60 | 60 | 0 | 0 | 0 |
| planet | 360 | 334 | 26 | 0 | 0 |

## 4. 不匹配字段

| Sample | Section | Body | Field | Local skill | PyJHora | Delta |
|---|---|---|---|---|---|---:|
| smoke_beijing_1990_noon | planet | Rahu | nakshatra | Dhanishta | Shravana |  |
| smoke_beijing_1990_noon | planet | Rahu | nakshatra_pada | 1 | 4 |  |
| smoke_beijing_1990_noon | planet | Rahu | degree_in_sign | 24.7353 | 23.141 | 1.5943 |
| smoke_beijing_1990_noon | planet | Ketu | nakshatra_pada | 3 | 2 |  |
| smoke_beijing_1990_noon | planet | Ketu | degree_in_sign | 24.7353 | 23.141 | 1.5943 |
| smoke_beijing_1990_noon | D9 | Rahu | sign | Leo | Cancer |  |
| smoke_beijing_1990_noon | D9 | Rahu | degree_in_sign | 12.6174 | 28.2689 | 15.6515 |
| smoke_beijing_1990_noon | D9 | Ketu | sign | Aquarius | Capricorn |  |
| smoke_beijing_1990_noon | D9 | Ketu | degree_in_sign | 12.6174 | 28.2689 | 15.6515 |
| smoke_beijing_1990_noon | D10 | Rahu | sign | Taurus | Aries |  |
| smoke_beijing_1990_noon | D10 | Rahu | degree_in_sign | 7.3526 | 21.4099 | 14.0573 |
| smoke_beijing_1990_noon | D10 | Ketu | sign | Scorpio | Libra |  |
| smoke_beijing_1990_noon | D10 | Ketu | degree_in_sign | 7.3526 | 21.4099 | 14.0573 |
| smoke_newyork_1985_morning | planet | Rahu | degree_in_sign | 21.246 | 22.5483 | 1.3023 |
| smoke_newyork_1985_morning | planet | Ketu | degree_in_sign | 21.246 | 22.5483 | 1.3023 |
| smoke_newyork_1985_morning | D9 | Rahu | degree_in_sign | 11.2143 | 22.9344 | 11.7201 |
| smoke_newyork_1985_morning | D9 | Ketu | degree_in_sign | 11.2143 | 22.9344 | 11.7201 |
| smoke_newyork_1985_morning | D10 | Rahu | degree_in_sign | 2.4603 | 15.4827 | 13.0224 |
| smoke_newyork_1985_morning | D10 | Ketu | degree_in_sign | 2.4603 | 15.4827 | 13.0224 |
| smoke_london_1970_evening | planet | Rahu | degree_in_sign | 17.6225 | 18.4125 | 0.79 |
| smoke_london_1970_evening | planet | Ketu | degree_in_sign | 17.6225 | 18.4125 | 0.79 |
| smoke_london_1970_evening | D9 | Rahu | degree_in_sign | 8.6025 | 15.7124 | 7.1099 |
| smoke_london_1970_evening | D9 | Ketu | degree_in_sign | 8.6025 | 15.7124 | 7.1099 |
| smoke_delhi_2000_midnight | planet | Rahu | degree_in_sign | 22.1972 | 21.616 | 0.5812 |
| smoke_delhi_2000_midnight | planet | Ketu | degree_in_sign | 22.1972 | 21.616 | 0.5812 |
| smoke_delhi_2000_midnight | D9 | Rahu | degree_in_sign | 19.7747 | 14.5444 | 5.2303 |
| smoke_delhi_2000_midnight | D9 | Ketu | degree_in_sign | 19.7747 | 14.5444 | 5.2303 |
| smoke_delhi_2000_midnight | D10 | Rahu | degree_in_sign | 11.9719 | 6.1604 | 5.8115 |
| smoke_delhi_2000_midnight | D10 | Ketu | degree_in_sign | 11.9719 | 6.1604 | 5.8115 |
| smoke_sydney_1999_afternoon | planet | Rahu | degree_in_sign | 17.2389 | 18.8586 | 1.6197 |
| smoke_sydney_1999_afternoon | planet | Ketu | degree_in_sign | 17.2389 | 18.8586 | 1.6197 |
| smoke_sydney_1999_afternoon | D9 | Rahu | degree_in_sign | 5.1499 | 19.7276 | 14.5777 |
| smoke_sydney_1999_afternoon | D9 | Ketu | degree_in_sign | 5.1499 | 19.7276 | 14.5777 |
| smoke_sydney_1999_afternoon | D10 | Rahu | sign | Leo | Virgo |  |
| smoke_sydney_1999_afternoon | D10 | Rahu | degree_in_sign | 22.3888 | 8.5862 | 13.8026 |
| smoke_sydney_1999_afternoon | D10 | Ketu | sign | Aquarius | Pisces |  |
| smoke_sydney_1999_afternoon | D10 | Ketu | degree_in_sign | 22.3888 | 8.5862 | 13.8026 |
| smoke_tokyo_1964_noon | planet | Rahu | degree_in_sign | 2.9977 | 1.9596 | 1.0381 |
| smoke_tokyo_1964_noon | planet | Ketu | degree_in_sign | 2.9977 | 1.9596 | 1.0381 |
| smoke_tokyo_1964_noon | D9 | Rahu | degree_in_sign | 26.9795 | 17.6361 | 9.3434 |
| smoke_tokyo_1964_noon | D9 | Ketu | degree_in_sign | 26.9795 | 17.6361 | 9.3434 |
| smoke_tokyo_1964_noon | D10 | Rahu | degree_in_sign | 29.9773 | 19.5957 | 10.3816 |
| smoke_tokyo_1964_noon | D10 | Ketu | degree_in_sign | 29.9773 | 19.5957 | 10.3816 |
| smoke_cairo_1952_dawn | planet | Rahu | degree_in_sign | 29.4558 | 28.3255 | 1.1303 |
| smoke_cairo_1952_dawn | planet | Ketu | degree_in_sign | 29.4558 | 28.3255 | 1.1303 |
| smoke_cairo_1952_dawn | D9 | Rahu | degree_in_sign | 25.1021 | 14.9291 | 10.173 |
| smoke_cairo_1952_dawn | D9 | Ketu | degree_in_sign | 25.1021 | 14.9291 | 10.173 |
| smoke_cairo_1952_dawn | D10 | Rahu | degree_in_sign | 24.5579 | 13.2545 | 11.3034 |
| smoke_cairo_1952_dawn | D10 | Ketu | degree_in_sign | 24.5579 | 13.2545 | 11.3034 |
| smoke_paris_1989_noon | planet | Rahu | degree_in_sign | 27.5276 | 28.0232 | 0.4956 |
| smoke_paris_1989_noon | planet | Ketu | degree_in_sign | 27.5276 | 28.0232 | 0.4956 |
| smoke_paris_1989_noon | D9 | Rahu | degree_in_sign | 7.7486 | 12.209 | 4.4604 |
| smoke_paris_1989_noon | D9 | Ketu | degree_in_sign | 7.7486 | 12.209 | 4.4604 |
| smoke_paris_1989_noon | D10 | Rahu | degree_in_sign | 5.2762 | 10.2322 | 4.956 |
| smoke_paris_1989_noon | D10 | Ketu | degree_in_sign | 5.2762 | 10.2322 | 4.956 |
| smoke_losangeles_1995_night | planet | Rahu | degree_in_sign | 11.3412 | 11.7412 | 0.4 |
| smoke_losangeles_1995_night | planet | Ketu | degree_in_sign | 11.3412 | 11.7412 | 0.4 |
| smoke_losangeles_1995_night | D9 | Rahu | degree_in_sign | 12.0704 | 15.671 | 3.6006 |
| smoke_losangeles_1995_night | D9 | Ketu | degree_in_sign | 12.0704 | 15.671 | 3.6006 |
| smoke_losangeles_1995_night | D10 | Rahu | degree_in_sign | 23.4116 | 27.4122 | 4.0006 |
| smoke_losangeles_1995_night | D10 | Ketu | degree_in_sign | 23.4116 | 27.4122 | 4.0006 |
| smoke_sao_paulo_2004_morning | planet | Rahu | nakshatra_pada | 3 | 2 |  |
| smoke_sao_paulo_2004_morning | planet | Rahu | degree_in_sign | 20.6362 | 19.622 | 1.0142 |
| smoke_sao_paulo_2004_morning | planet | Ketu | nakshatra | Vishakha | Swati |  |
| smoke_sao_paulo_2004_morning | planet | Ketu | nakshatra_pada | 1 | 4 |  |
| smoke_sao_paulo_2004_morning | planet | Ketu | degree_in_sign | 20.6362 | 19.622 | 1.0142 |
| smoke_sao_paulo_2004_morning | D10 | Rahu | degree_in_sign | 26.3619 | 16.2197 | 10.1422 |
| smoke_sao_paulo_2004_morning | D10 | Ketu | degree_in_sign | 26.3619 | 16.2197 | 10.1422 |

## 4b. 边界敏感字段

| Sample | Section | Body | Field | Local skill | PyJHora | Delta |
|---|---|---|---|---|---|---:|
| smoke_london_1970_evening | D10 | Rahu | sign | Cancer | Leo |  |
| smoke_london_1970_evening | D10 | Rahu | degree_in_sign | 26.225 | 4.1249 | 22.1001 |
| smoke_london_1970_evening | D10 | Ketu | sign | Capricorn | Aquarius |  |
| smoke_london_1970_evening | D10 | Ketu | degree_in_sign | 26.225 | 4.1249 | 22.1001 |
| smoke_sao_paulo_2004_morning | D9 | Rahu | sign | Libra | Virgo |  |
| smoke_sao_paulo_2004_morning | D9 | Rahu | degree_in_sign | 5.7257 | 26.5977 | 20.872 |
| smoke_sao_paulo_2004_morning | D9 | Ketu | sign | Aries | Pisces |  |
| smoke_sao_paulo_2004_morning | D9 | Ketu | degree_in_sign | 5.7257 | 26.5977 | 20.872 |

## 5. 判断

- PyJHora 作为第二开源引擎已经接入成功。
- D1/D9/D10若高匹配，说明当前 skill 的分盘算法不仅与 Swiss direct 自算一致，也能通过独立 Jyotish 项目的实测。
- Dasha 部分若存在系统性差异，优先视为 PyJHora seed_star / dasha year / 起运规则口径差异，不能马上判定本 skill 错；需要 JHora 或 Drik Panchang 再仲裁。
- PyJHora 是 AGPL-3.0，适合做外部 benchmark，不适合把其源码或派生实现并入当前 skill。