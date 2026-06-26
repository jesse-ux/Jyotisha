# First Tajika/Sahams Annual Oracle Packet Operator Card

Goal: fill one external annual-chart packet for `template_steve_jobs_varshaphala_1984_lahiri`.

This is for Varshaphala / Tajika / Sahams only. Do not use local `scripts/varshaphala.py` output as evidence.

## Birth And Year

- Birth date: `1955-02-24`
- Birth time: `19:15:00`
- Birth place: San Francisco, CA
- Coordinates: `37.7749, -122.4194`
- Birth timezone: `UTC-08:00`
- Ayanamsa: `Lahiri`
- Node mode: `true node`
- Target annual year: `1984`

## External Tool

Use one external black-box source:

- JHora Varshaphala/Tajika annual chart screen, or
- PyJHora black-box annual output, or
- a printed Tajika/Varshaphala example.

Record the solar-return convention in `metadata.operator_note`, including timezone/DST and whether the tool calculates the annual chart at exact solar return.

## Fill This Packet

Template:

`references/oracle/evidence_packet_templates/tajika_steve_jobs_1984_first_packet.json`

Required metadata:

- `status`: set to `external_verified`
- `metadata.tool_name`
- `metadata.tool_version_or_url`
- `metadata.capture_date`
- `metadata.source_artifact`
- `metadata.operator_note`

Required target fields:

- `target.solar_return_datetime`
- `target.varsha_lagna_deg`
- `target.muntha_sign`
- `target.year_lord`
- `target.mudda_dasha_first_lord`
- `target.sahams.punya_saham`
- `target.sahams.rajya_saham`
- `target.sahams.vivah_saham`
- `target.tajika_yogas`
- `target.source_artifact`

Save the redacted screenshot, stdout snippet, or book citation under `references/oracle/artifacts/`.

## Screen Checklist

Capture only what is needed:

1. Settings screen: ayanamsa, node mode, location, target year and solar-return convention.
2. Varshaphala chart: solar return datetime and Varsha Lagna.
3. Muntha / Year Lord screen: Muntha sign and Year Lord.
4. Mudda Dasha screen: first Mudda Dasha lord.
5. Sahams screen: Punya Saham, Rajya Saham and Vivah Saham.
6. Tajika Yogas screen: visible yogas such as Ithasala, Easarapha, Nakta or other tool labels.

## Apply

```bash
python3 scripts/tajika_annual_oracle_queue.py \
  --oracle-file references/oracle/tajika_annual_oracle_cases.json \
  --apply-packet references/oracle/evidence_packet_templates/tajika_steve_jobs_1984_first_packet.json \
  --format json
```

## Validate

```bash
python3 scripts/tajika_annual_oracle_queue.py \
  --oracle-file references/oracle/tajika_annual_oracle_cases.json \
  --format json

python3 scripts/tajika_annual_benchmark_dashboard.py \
  --oracle-file references/oracle/tajika_annual_oracle_cases.json \
  --format json
```

Expected first milestone after real external evidence is filled:

- Tajika/Sahams annual closure board moves from `external_verified_annual_tasks: 0` to at least `1`.
- Master dashboard still keeps `can_claim_global_oracle_closure: false` until all external oracle fronts are complete.
