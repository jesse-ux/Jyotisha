# Jyotish benchmark 第四轮：Rahu/Ketu 节点口径仲裁

生成时间：2026-06-03

## 1. 本轮目的

- 解释第三轮 PyJHora 对比中 Rahu/Ketu 大量差异的根因。
- 对比当前 skill canonical baseline 与 Swiss Ephemeris Mean Node、Swiss Ephemeris True Node、PyJHora rasi_chart 默认输出。
- 样本仍为10个公开/虚构 smoke case，不包含用户个人资料。

## 2. 总体结果

| Target | Total | Match | Mismatch | Match rate |
|---|---:|---:|---:|---:|
| swiss_mean_node | 80 | 80 | 0 | 100.00% |
| swiss_true_node | 80 | 54 | 26 | 67.50% |
| pyjhora_default_rasi | 80 | 54 | 26 | 67.50% |

## 3. 分字段统计

| Target | Field | Total | Match | Mismatch |
|---|---|---:|---:|---:|
| swiss_mean_node | sign | 20 | 20 | 0 |
| swiss_mean_node | degree_in_sign | 20 | 20 | 0 |
| swiss_mean_node | nakshatra | 20 | 20 | 0 |
| swiss_mean_node | nakshatra_pada | 20 | 20 | 0 |
| swiss_true_node | sign | 20 | 20 | 0 |
| swiss_true_node | degree_in_sign | 20 | 0 | 20 |
| swiss_true_node | nakshatra | 20 | 18 | 2 |
| swiss_true_node | nakshatra_pada | 20 | 16 | 4 |
| pyjhora_default_rasi | sign | 20 | 20 | 0 |
| pyjhora_default_rasi | degree_in_sign | 20 | 0 | 20 |
| pyjhora_default_rasi | nakshatra | 20 | 18 | 2 |
| pyjhora_default_rasi | nakshatra_pada | 20 | 16 | 4 |

## 4. 关键不匹配样例

| Sample | Target | Body | Field | Local skill | Target value | Delta |
|---|---|---|---|---|---|---:|
| smoke_beijing_1990_noon | swiss_true_node | Rahu | nakshatra | Dhanishta | Shravana |  |
| smoke_beijing_1990_noon | swiss_true_node | Rahu | nakshatra_pada | 1 | 4 |  |
| smoke_beijing_1990_noon | swiss_true_node | Rahu | degree_in_sign | 24.7353 | 23.140989 | 1.594311 |
| smoke_beijing_1990_noon | swiss_true_node | Ketu | nakshatra_pada | 3 | 2 |  |
| smoke_beijing_1990_noon | swiss_true_node | Ketu | degree_in_sign | 24.7353 | 23.140989 | 1.594311 |
| smoke_beijing_1990_noon | pyjhora_default_rasi | Rahu | nakshatra | Dhanishta | Shravana |  |
| smoke_beijing_1990_noon | pyjhora_default_rasi | Rahu | nakshatra_pada | 1 | 4 |  |
| smoke_beijing_1990_noon | pyjhora_default_rasi | Rahu | degree_in_sign | 24.7353 | 23.140989 | 1.594311 |
| smoke_beijing_1990_noon | pyjhora_default_rasi | Ketu | nakshatra_pada | 3 | 2 |  |
| smoke_beijing_1990_noon | pyjhora_default_rasi | Ketu | degree_in_sign | 24.7353 | 23.140989 | 1.594311 |
| smoke_newyork_1985_morning | swiss_true_node | Rahu | degree_in_sign | 21.246 | 22.548271 | 1.302271 |
| smoke_newyork_1985_morning | swiss_true_node | Ketu | degree_in_sign | 21.246 | 22.548271 | 1.302271 |
| smoke_newyork_1985_morning | pyjhora_default_rasi | Rahu | degree_in_sign | 21.246 | 22.548271 | 1.302271 |
| smoke_newyork_1985_morning | pyjhora_default_rasi | Ketu | degree_in_sign | 21.246 | 22.548271 | 1.302271 |
| smoke_london_1970_evening | swiss_true_node | Rahu | degree_in_sign | 17.6225 | 18.41249 | 0.78999 |
| smoke_london_1970_evening | swiss_true_node | Ketu | degree_in_sign | 17.6225 | 18.41249 | 0.78999 |
| smoke_london_1970_evening | pyjhora_default_rasi | Rahu | degree_in_sign | 17.6225 | 18.41249 | 0.78999 |
| smoke_london_1970_evening | pyjhora_default_rasi | Ketu | degree_in_sign | 17.6225 | 18.41249 | 0.78999 |
| smoke_delhi_2000_midnight | swiss_true_node | Rahu | degree_in_sign | 22.1972 | 21.616044 | 0.581156 |
| smoke_delhi_2000_midnight | swiss_true_node | Ketu | degree_in_sign | 22.1972 | 21.616044 | 0.581156 |
| smoke_delhi_2000_midnight | pyjhora_default_rasi | Rahu | degree_in_sign | 22.1972 | 21.616044 | 0.581156 |
| smoke_delhi_2000_midnight | pyjhora_default_rasi | Ketu | degree_in_sign | 22.1972 | 21.616044 | 0.581156 |
| smoke_sydney_1999_afternoon | swiss_true_node | Rahu | degree_in_sign | 17.2389 | 18.858624 | 1.619724 |
| smoke_sydney_1999_afternoon | swiss_true_node | Ketu | degree_in_sign | 17.2389 | 18.858624 | 1.619724 |
| smoke_sydney_1999_afternoon | pyjhora_default_rasi | Rahu | degree_in_sign | 17.2389 | 18.858624 | 1.619724 |
| smoke_sydney_1999_afternoon | pyjhora_default_rasi | Ketu | degree_in_sign | 17.2389 | 18.858624 | 1.619724 |
| smoke_tokyo_1964_noon | swiss_true_node | Rahu | degree_in_sign | 2.9977 | 1.959571 | 1.038129 |
| smoke_tokyo_1964_noon | swiss_true_node | Ketu | degree_in_sign | 2.9977 | 1.959571 | 1.038129 |
| smoke_tokyo_1964_noon | pyjhora_default_rasi | Rahu | degree_in_sign | 2.9977 | 1.959571 | 1.038129 |
| smoke_tokyo_1964_noon | pyjhora_default_rasi | Ketu | degree_in_sign | 2.9977 | 1.959571 | 1.038129 |
| smoke_cairo_1952_dawn | swiss_true_node | Rahu | degree_in_sign | 29.4558 | 28.325454 | 1.130346 |
| smoke_cairo_1952_dawn | swiss_true_node | Ketu | degree_in_sign | 29.4558 | 28.325454 | 1.130346 |
| smoke_cairo_1952_dawn | pyjhora_default_rasi | Rahu | degree_in_sign | 29.4558 | 28.325453 | 1.130347 |
| smoke_cairo_1952_dawn | pyjhora_default_rasi | Ketu | degree_in_sign | 29.4558 | 28.325453 | 1.130347 |
| smoke_paris_1989_noon | swiss_true_node | Rahu | degree_in_sign | 27.5276 | 28.023225 | 0.495625 |
| smoke_paris_1989_noon | swiss_true_node | Ketu | degree_in_sign | 27.5276 | 28.023225 | 0.495625 |
| smoke_paris_1989_noon | pyjhora_default_rasi | Rahu | degree_in_sign | 27.5276 | 28.023225 | 0.495625 |
| smoke_paris_1989_noon | pyjhora_default_rasi | Ketu | degree_in_sign | 27.5276 | 28.023225 | 0.495625 |
| smoke_losangeles_1995_night | swiss_true_node | Rahu | degree_in_sign | 11.3412 | 11.741225 | 0.400025 |
| smoke_losangeles_1995_night | swiss_true_node | Ketu | degree_in_sign | 11.3412 | 11.741225 | 0.400025 |
| smoke_losangeles_1995_night | pyjhora_default_rasi | Rahu | degree_in_sign | 11.3412 | 11.741225 | 0.400025 |
| smoke_losangeles_1995_night | pyjhora_default_rasi | Ketu | degree_in_sign | 11.3412 | 11.741225 | 0.400025 |
| smoke_sao_paulo_2004_morning | swiss_true_node | Rahu | nakshatra_pada | 3 | 2 |  |
| smoke_sao_paulo_2004_morning | swiss_true_node | Rahu | degree_in_sign | 20.6362 | 19.621972 | 1.014228 |
| smoke_sao_paulo_2004_morning | swiss_true_node | Ketu | nakshatra | Vishakha | Swati |  |
| smoke_sao_paulo_2004_morning | swiss_true_node | Ketu | nakshatra_pada | 1 | 4 |  |
| smoke_sao_paulo_2004_morning | swiss_true_node | Ketu | degree_in_sign | 20.6362 | 19.621972 | 1.014228 |
| smoke_sao_paulo_2004_morning | pyjhora_default_rasi | Rahu | nakshatra_pada | 3 | 2 |  |
| smoke_sao_paulo_2004_morning | pyjhora_default_rasi | Rahu | degree_in_sign | 20.6362 | 19.621972 | 1.014228 |
| smoke_sao_paulo_2004_morning | pyjhora_default_rasi | Ketu | nakshatra | Vishakha | Swati |  |
| smoke_sao_paulo_2004_morning | pyjhora_default_rasi | Ketu | nakshatra_pada | 1 | 4 |  |
| smoke_sao_paulo_2004_morning | pyjhora_default_rasi | Ketu | degree_in_sign | 20.6362 | 19.621972 | 1.014228 |

## 5. 仲裁结论

- 当前 skill 的 Rahu/Ketu 与 Swiss Ephemeris **Mean Node** 口径完全一致；这解释了第一轮 Swiss direct 450/450 匹配。
- PyJHora 4.8.6 的 `rasi_chart()` 默认走 `drik.dhasavarga(... set_rahu_ketu_as_true_nodes=True)`，即默认使用 **True Node**。
- 因此第三轮 PyJHora 中 Rahu/Ketu 的 degree/nakshatra/D9/D10 差异，主要不是当前 skill 的计算 bug，而是 **Mean Node vs True Node 口径差异**。
- 工程建议：当前 skill 应显式声明默认 `node_mode=mean`，后续可新增 `--node-mode mean|true` 参数；benchmark 报告中也应把节点口径列为冻结参数。