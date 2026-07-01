# First External Oracle Packet Assistant

- front: `tajika_sahams`
- case_id: `template_einstein_varshaphala_1905_lahiri`
- capture_id: `external_template_einstein_varshaphala_1905_lahiri`
- ready_to_apply: `false`
- operator_card: `docs/benchmark/tajika_einstein_1905_first_packet_operator_card.md`
- packet_template: `references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json`

## Missing Summary

- metadata: `0`
- target: `4`

## Prefilled Fields

- status: `external_verified`
- promotion_status_after_fill: `external_verified`

- metadata:

  - tool_name: `PyJHora`
  - tool_version_or_url: `PyJHora 4.8.6 isolated workbuddy black-box run`
  - capture_date: `2026-06-29`
  - source_artifact: `references/oracle/artifacts/pyjhora_einstein_varshaphala_1905_lahiri_partial_20260629.txt`
  - ayanamsa: `lahiri`
  - node_mode: `mean`
  - timezone: `UTC+00:53`
  - annual_system: `Varshaphala/Tajika`
  - target_year: `1905`
  - operator_note: `Black-box annual output from workbuddy PyJHora 4.8.6 environment. External evidence only; local annual engine output was not used. Solar-return timestamp, Varsha Lagna, Muntha, Year Lord, first Mudda Dasha lord, selected Sahams, and Tajika Yogas were captured through the external PyJHora path via the annual chart and jhora.horoscope.transit.tajaka_yoga helper chain.`

- settings:

  - ayanamsa: `lahiri`
  - node_mode: `mean`
  - annual_system: `varshaphala`
  - target_year: `1905`


## Manual Fill Plan

- status_value: `external_verified`
- manual_entry_count: `4`

## Missing Fields

- `target.tajika_yogas.gairi_kamboola`
- `target.tajika_yogas.khallasara`
- `target.tajika_yogas.nakta`
- `target.tajika_yogas.yamaya`

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
