# Jyotish benchmark 第一轮本地基线报告

生成时间：2026-06-03

## 1. 本轮范围

- 本轮只建立当前 skill 的 canonical baseline。
- 样本全部为公开/虚构 smoke test，不包含用户个人出生资料。
- 还没有接入 PyJHora / VedAstro / jyotishyamitra 等外部引擎，因此本轮不能给最终可信度评分。

## 2. 执行结果

- 样本数：10
- 成功：10
- 失败：0
- 输出目录：`jyotish_benchmark/outputs/`

## 3. 样本摘要

| Sample | Ascendant | MD/AD | A10 | Modules | Empty modules |
|---|---|---|---|---:|---|
| smoke_beijing_1990_noon | {'sign': 'Pisces', 'sign_cn': '双鱼座', 'degree': 348.1199, 'degree_in_sign': 18.1199, 'lord': 'Jupiter'} | Saturn / Saturn | Virgo | 27 | - |
| smoke_newyork_1985_morning | {'sign': 'Leo', 'sign_cn': '狮子座', 'degree': 120.7023, 'degree_in_sign': 0.7023, 'lord': 'Sun'} | Jupiter / Saturn | Aquarius | 27 | - |
| smoke_london_1970_evening | {'sign': 'Virgo', 'sign_cn': '处女座', 'degree': 158.3003, 'degree_in_sign': 8.3003, 'lord': 'Mercury'} | Jupiter / Venus | Virgo | 27 | - |
| smoke_delhi_2000_midnight | {'sign': 'Virgo', 'sign_cn': '处女座', 'degree': 155.7304, 'degree_in_sign': 5.7304, 'lord': 'Mercury'} | Venus / Mercury | Pisces | 27 | - |
| smoke_sydney_1999_afternoon | {'sign': 'Capricorn', 'sign_cn': '摩羯座', 'degree': 298.7176, 'degree_in_sign': 28.7176, 'lord': 'Saturn'} | Moon / Rahu | Capricorn | 27 | - |
| smoke_tokyo_1964_noon | {'sign': 'Sagittarius', 'sign_cn': '射手座', 'degree': 251.5357, 'degree_in_sign': 11.5357, 'lord': 'Jupiter'} | Moon / Venus | Gemini | 27 | - |
| smoke_cairo_1952_dawn | {'sign': 'Cancer', 'sign_cn': '巨蟹座', 'degree': 98.5969, 'degree_in_sign': 8.5969, 'lord': 'Moon'} | Rahu / Ketu | Capricorn | 27 | - |
| smoke_paris_1989_noon | {'sign': 'Sagittarius', 'sign_cn': '射手座', 'degree': 252.1586, 'degree_in_sign': 12.1586, 'lord': 'Jupiter'} | Mercury / Jupiter | Scorpio | 27 | - |
| smoke_losangeles_1995_night | {'sign': 'Sagittarius', 'sign_cn': '射手座', 'degree': 254.083, 'degree_in_sign': 14.083, 'lord': 'Jupiter'} | Mercury / Rahu | Capricorn | 27 | - |
| smoke_sao_paulo_2004_morning | {'sign': 'Pisces', 'sign_cn': '双鱼座', 'degree': 358.4495, 'degree_in_sign': 28.4495, 'lord': 'Jupiter'} | Jupiter / Jupiter | Aries | 27 | - |

## 4. 发现

- 当前 skill 对 10 个 smoke 样本都能生成 full-reading canonical JSON。
- 这证明内部输出契约具备批量 benchmark 的基础。
- 但这只是 baseline，不是外部可信度证明。
- 下一步必须接入至少 PyJHora 和 jyotishyamitra，形成 cross-engine matrix。

## 5. 下一步

1. 安装/隔离运行 PyJHora，抽取 D1/D9/D10/Dasha。
2. 安装/隔离运行 jyotishyamitra，抽取 JSON 输出。
3. 若 VedAstro API 可用，加入 API 对比；否则列为人工/半自动。
4. 生成 `cross_engine_matrix.csv`，按字段计算一致/不一致/不可比。
5. 对边界样本单独标注，避免误判。