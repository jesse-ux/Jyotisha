# Antigravity AI 开源参考复核与 Oracle 采集可行性 (Round 3)

## 可行性分析

- **VedAstro.Python / HTTP API (MIT)**：适合批量抽取星体黄经和排盘的基础元数据。注意调用时部分对象属性（如 `TotalDegrees`）映射存在坑，直接调 HTTP API 并解析 JSON 最稳妥。
- **PyJHora (AGPL-3.0) / JHora**：许可证限制较严，只能作为外部计算黑盒参考，决不能将任何实现代码（特别是 Shadbala / Dasha 计算系数与时间常量）复制入本项目。我们可通过手动截图并结构化录入作为我们的 `external_verified` 基准。
- **Swiss Ephemeris**：本身开源基石，但其全局的 sidereal mode 和 ayanamsa 状态在并发/跨请求环境存在潜在副作用，当前本项目的 `_apply_ayanamsa()` 已处理该全局锁问题。

## Oracle Case 字段模板 (不少于 5 个)

```json
[
  {
    "id": "template_private_oracle_redacted",
    "status": "template_only",
    "source": "JHora/PyJHora/VedAstro/Manual screenshot",
    "birth": {
      "year": REDACTED_YEAR,
      "month": 4,
      "day": 17,
      "hour": 14,
      "minute": 45,
      "second": 20,
      "lat": 36.466667,
      "lon": 114.2,
      "tz": 8
    },
    "settings": {
      "ayanamsa": "lahiri",
      "node_mode": "mean"
    },
    "target": {
      "moon_sidereal_longitude_deg": null,
      "vimshottari_start_date": null,
      "shadbala_components": null
    },
    "verification_note": "Only fill target fields when the value comes from external oracle, not from this repo."
  },
  {
    "id": "template_steve_jobs_dasha_lahiri",
    "status": "template_only",
    "source": "JHora PDF Screenshot",
    "birth": {
      "year": 1955,
      "month": 2,
      "day": 24,
      "hour": 19,
      "minute": 15,
      "second": 0,
      "lat": 37.7749,
      "lon": -122.4194,
      "tz": -8
    },
    "settings": {
      "ayanamsa": "lahiri",
      "node_mode": "true"
    },
    "target": {
      "vimshottari_start_date": null,
      "shadbala_components": null
    },
    "verification_note": "Verify Dasha boundaries."
  },
  {
    "id": "template_redacted_place_shadbala_raman",
    "status": "template_only",
    "source": "VedAstro API",
    "birth": {
      "year": 1980,
      "month": 1,
      "day": 1,
      "hour": 12,
      "minute": 0,
      "second": 0,
      "lat": 36.466667,
      "lon": 114.2,
      "tz": 8
    },
    "settings": {
      "ayanamsa": "raman",
      "node_mode": "mean"
    },
    "target": {
      "moon_sidereal_longitude_deg": null,
      "shadbala_components": null
    },
    "verification_note": "Validate Raman Ayanamsa effect on Shadbala."
  },
  {
    "id": "template_extreme_latitude_kp",
    "status": "template_only",
    "source": "PyJHora output",
    "birth": {
      "year": 2000,
      "month": 6,
      "day": 21,
      "hour": 0,
      "minute": 0,
      "second": 0,
      "lat": 65.0,
      "lon": 15.0,
      "tz": 1
    },
    "settings": {
      "ayanamsa": "kp",
      "node_mode": "true"
    },
    "target": {
      "ascendant_longitude_deg": null,
      "shadbala_components": null
    },
    "verification_note": "High latitude testing with KP ayanamsa."
  },
  {
    "id": "template_historical_epoch_lahiri",
    "status": "template_only",
    "source": "JHora Offline Tool",
    "birth": {
      "year": 1800,
      "month": 1,
      "day": 1,
      "hour": 12,
      "minute": 0,
      "second": 0,
      "lat": 28.6139,
      "lon": 77.2090,
      "tz": 5.5
    },
    "settings": {
      "ayanamsa": "lahiri",
      "node_mode": "mean"
    },
    "target": {
      "sun_sidereal_longitude_deg": null,
      "vimshottari_start_date": null
    },
    "verification_note": "Test deep historical epoch precision."
  }
]
```
