# Tajika Einstein 1905 Copy-Ready Checklist

Packet:
`references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json`

Steve Jobs sample:
`references/oracle/artifacts/pending_packets/external_template_steve_jobs_varshaphala_1984_lahiri_pyjhora_20260627.json`

Use one external source only:
- `JHora`
- `PyJHora`
- printed Tajika/Varshaphala example

Do not use local `scripts/varshaphala.py` output as evidence.

## Copy Steve Jobs Pattern Directly

Copy the same writing pattern for:

- `status`: set to `external_verified` only after all fields below are filled
- `metadata.tool_name`
- `metadata.tool_version_or_url`
- `metadata.capture_date`
- `metadata.source_artifact`
- `metadata.operator_note`
- `target.source_artifact`

Recommended metadata pattern:

- `metadata.tool_name`: `PyJHora` or `JHora`
- `metadata.tool_version_or_url`: version string or source citation
- `metadata.capture_date`: `YYYY-MM-DD`
- `metadata.source_artifact`: `references/oracle/artifacts/<your-evidence-file>`
- `metadata.operator_note`: note ayanamsa, node mode, timezone, solar-return convention, and any workaround
- `target.source_artifact`: same artifact path as above

## Must Fill From External Source

These values must be copied from the external annual-chart source, not inferred locally:

- `target.solar_return_datetime`
- `target.varsha_lagna_deg`
- `target.muntha_sign`
- `target.year_lord`
- `target.mudda_dasha_first_lord`
- `target.sahams.punya_saham`
- `target.sahams.rajya_saham`
- `target.sahams.vivah_saham`
- `target.tajika_yogas`

## Fast Fill Order

1. Fill metadata first:
   - `metadata.tool_name`
   - `metadata.tool_version_or_url`
   - `metadata.capture_date`
   - `metadata.source_artifact`
   - `metadata.operator_note`

2. Fill annual header:
   - `target.solar_return_datetime`
   - `target.varsha_lagna_deg`

3. Fill annual rulership:
   - `target.muntha_sign`
   - `target.year_lord`
   - `target.mudda_dasha_first_lord`

4. Fill Sahams:
   - `target.sahams.punya_saham`
   - `target.sahams.rajya_saham`
   - `target.sahams.vivah_saham`

5. Fill yoga block:
   - `target.tajika_yogas`

6. Set:
   - `target.source_artifact`
   - `status = external_verified`

## Minimal Screen / Output Capture

Capture only these:

1. Settings / source header
2. Solar return datetime
3. Varsha Lagna
4. Muntha + Year Lord
5. First Mudda Dasha lord
6. Sahams block
7. Tajika Yogas block

## Final Apply / Validate

```bash
python3 scripts/tajika_annual_oracle_queue.py \
  --oracle-file references/oracle/tajika_annual_oracle_cases.json \
  --apply-packet references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json \
  --format json
```

```bash
python3 scripts/tajika_annual_benchmark_dashboard.py \
  --oracle-file references/oracle/tajika_annual_oracle_cases.json \
  --format json
```
