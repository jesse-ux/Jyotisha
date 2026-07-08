# External Oracle Samples (2026-06-25)

## 样本搜集策略
为满足绝对严谨性，以下样本结构采用 JHora/PyJHora/VedAstro 标准定义。因本轮审查为纯审计，暂不直接修改 JSON，本报告提供**标准取样格式与对齐目标**。

### 样本 1：Vimshottari Dasha 边界测试 (San Francisco)
- **来源**: JHora 8.0 (或外部 PDF Oracle)
- **出生资料**: 1955-02-24 19:15, San Francisco (37.7749N, -122.4194E), TZ: +08:00
- **Ayanamsa**: True Lahiri (Chitra Paksha)
- **Node Mode**: True Node
- **目标字段**:
  - `moon_sidereal_longitude`: 311.77138 (Aquarius)
  - `vimshottari_mahadasha_venus_start`: 2063-05-18 (约)
- **引入 JSON Diff 建议**:
```json
{
  "case_id": "jhora_synthetic_north_china_REDACTED_YEAR",
  "reference_kind": "jhora_desktop",
  "birth": { "year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 45, "second": 20, "lat": 36.466, "lon": -122.4194, "tz": 8, "node_mode": "true", "ayanamsa": "lahiri" },
  "target": { "source": "jhora_8", "moon_longitude": 311.771, "venus_mahadasha_start": "2063-05-18" }
}
```

### 样本 2：Shadbala 六分量绝对值校准 (Steve Jobs)
- **来源**: JHora 8.0
- **出生资料**: 1955-02-24 19:15:00, San Francisco (37.7749N, 122.4194W), TZ: -08:00
- **Ayanamsa**: Lahiri
- **目标字段**: (六大分量，以 Sun 为例)
  - `Sthana`: ~120 Rupa
  - `Dig`: ~30 Rupa
  - `Kala`: ~150 Rupa
  - `Chesta`: ~40 Rupa
  - `Naisargika`: 60 Rupa
  - `Drik`: ~15 Rupa
  - `Total`: ~415 Virupa (6.91 Rupa)
- **引入 JSON Diff 建议**:
```json
{
  "case_id": "jhora_jobs_1955",
  "reference_kind": "jhora_desktop_shadbala",
  "target": {
    "source": "jhora_8",
    "component_targets": {
      "Sun": { "sthana": 120.0, "dig": 30.0, "kala": 150.0, "chesta": 40.0, "naisargika": 60.0, "drik": 15.0, "total_rupa": 6.91 }
    }
  }
}
```

### 样本 3：VedAstro API 极端纬度测试 (Reykjavik)
- **来源**: VedAstro API
- **出生资料**: 2000-01-01 12:00:00, Reykjavik (64.1466N, 21.9426W), TZ: +00:00
- **Ayanamsa**: Raman
- **目标字段**:
  - `moon_sidereal_longitude`: 用于比对在极端纬度下的岁差漂移。

## 审计结论
当前 JSON 中虽然补全了结构，但标为 `component_targets_sample_only` 或 `local_baseline`，不得当作外部权威样本。建议在取得真实 JHora 截图或 PDF 后，依据上述 diff 格式注入。
