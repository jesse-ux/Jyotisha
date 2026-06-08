# Jyotish Benchmark Round 10 — 解释层回归与置信度声明审计

日期：2026-06-04

## 目标

确认前几轮计算层修复和能力降级已经进入解释层与输出模板，避免出现以下问题：

1. Chara Dasha 已经降级为 `partial`，但文档或输出仍把它当作高置信度应期模块。
2. Shadbala 已经降级为 `partial`，但仍声称完成传统绝对值校准。
3. full-reading Transit 已修复为真实过境，但解释层仍可能不声明 `true_transit_positions`。
4. Ashtakavarga v2.1 已经完成 BPHS/PVR 书例校准，但输出或文档未体现。

## 本轮修正

### 1. Jaimini / Chara Dasha 表述降权

修正文件：

- `README.md`
- `assets/timing-prediction-template.md`
- `references/strict-workflow-router.md`
- `scripts/jaimini.py`
- `scripts/jyotish_engine.py`

关键变化：

- Jaimini 静态层保留：Chara Karaka、AK/AmK、Karakamsha。
- Chara Dasha timing 明确为 `partial`。
- 在 `full-reading.modules.jaimini` 中新增：

```json
"chara_dasha_capability": {
  "status": "partial",
  "reason": "Round 7 vs PyJHora KN Rao matched 58/240 fields; current implementation is simplified, not full KN Rao/PVN Rao/Iranganti.",
  "usage_rule": "Use Chara Karaka/Karakamsha normally; use Chara Dasha timing only as low-weight corroboration."
}
```

### 2. Shadbala 表述降权

修正文件：

- `scripts/shadbala.py`
- `scripts/report_builder.py`

关键变化：

- `scripts/shadbala.py` 不再称为“完整 Shadbala”。
- 输出 method 改为：

```text
Shadbala六重力量（内部一致相对强弱；外部绝对值校准前partial）
```

- 报告封面中的量化指标改为：

```text
Shadbala (relative/partial), Ashtakavarga v2.1 (SAV/BAV), D9 Navamsha
```

### 3. Technique Audit Table 模板修正

`references/strict-workflow-router.md` 中 Technique Audit Table 已明确：

- `Jaimini / Chara Dasha` 状态可为 `Used / partial / not used`。
- `Shadbala` 状态可为 `Used / partial / not used`。
- 两者都必须说明对置信度的影响。

## 回归抽查结果

代表性命令：

```bash
python3 scripts/jyotish_engine.py full-reading \
  --year 1990 --month 1 --day 1 --hour 12 --minute 0 \
  --lat 39.9042 --lon 116.4074 --tz 8 \
  --today 2026-06-04 --transit-date 2026-06-04
```

关键输出：

| 检查项 | 结果 |
|---|---|
| full-reading errors | `[]` |
| registry problem_count | `0` |
| registry warning_count | `0` |
| status_counts.covered | `12` |
| status_counts.partial | `4` |
| `modules.transit_positions.data_layer` | `true_transit_positions` |
| `modules.transit_multi_reference.data_layer` | `true_transit_positions` |
| `modules.transit_positions.target_date` | `2026-06-04` |
| `modules.ashtakavarga.method` | `Ashtakavarga八分法（BPHS/PVR书例校准v2.1）` |
| `modules.shadbala.method` | `Shadbala六重力量（内部一致相对强弱；外部绝对值校准前partial）` |
| `modules.jaimini.chara_dasha_capability.status` | `partial` |

## career_timing_strict audit table 抽查

| Technique | Status | Limitation present | Output paths |
|---|---|---:|---|
| `jaimini_chara_dasha` | `partial` | yes | `modules.jaimini` |
| `a10_karma_pada` | `covered` | no | `modules.special_lagnas.A10_Karma_Pada` |
| `shadbala` | `partial` | yes | `modules.shadbala` |
| `ashtakavarga` | `covered` | no | `modules.ashtakavarga` |

## 结论

第十轮解释层回归通过。当前 skill 已经把计算层可信度变化同步到解释层：

- Chara Dasha 不再被包装成高置信度完整应期模块。
- Shadbala 不再声称完成外部绝对值校准。
- full-reading Transit 明确输出真实过境数据层。
- Ashtakavarga 输出保留 v2.1 BPHS/PVR 书例校准口径。

下一步可以进入本地提交与 GitHub 同步阶段；若要继续提高可信度，则应优先实装并对标 KN Rao/PVN Rao Chara Dasha，或接入 JHora/公开书例完成 Shadbala 外部绝对值校准。
