# First External Oracle Packet Assistant

- front: `tajika_sahams`
- case_id: `template_einstein_varshaphala_1905_lahiri`
- capture_id: `external_template_einstein_varshaphala_1905_lahiri`
- ready_to_apply: `false`
- operator_card: `docs/benchmark/tajika_einstein_1905_first_packet_operator_card.md`
- packet_template: `references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json`

## Missing Summary

- metadata: `5`
- target: `10`

## Prefilled Fields

- status: `draft`
- promotion_status_after_fill: `external_verified`

- metadata:

  - ayanamsa: `lahiri`
  - node_mode: `mean`
  - timezone: `0.883333`
  - annual_system: `varshaphala`
  - target_year: `1905`

- settings:

  - ayanamsa: `lahiri`
  - node_mode: `mean`
  - annual_system: `varshaphala`
  - target_year: `1905`


## Manual Fill Plan

- status_value: `external_verified`
- manual_entry_count: `15`

## Missing Fields

- `metadata.tool_name`
- `metadata.tool_version_or_url`
- `metadata.capture_date`
- `metadata.operator_note`
- `metadata.source_artifact`
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

## External Sources

- JHora Varshaphala/Tajika annual chart screen
- PyJHora black-box annual output
- printed Tajika/Varshaphala example

## Apply

```bash
python3 scripts/tajika_annual_oracle_queue.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --apply-packet references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json --format json
```

## Validate

```bash
python3 scripts/tajika_annual_oracle_queue.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --format json && python3 scripts/tajika_annual_benchmark_dashboard.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --format json
```

## Boundary

This assistant only reports what to fill. It must not invent external oracle values, must not use local engine output as evidence, and must not copy incompatible external code.
