# First External Oracle Packet Assistant

- front: `tajika_sahams`
- case_id: `template_steve_jobs_varshaphala_1984_lahiri`
- capture_id: `external_template_steve_jobs_varshaphala_1984_lahiri`
- ready_to_apply: `false`
- operator_card: `docs/benchmark/tajika_steve_jobs_1984_first_packet_operator_card.md`
- packet_template: `references/oracle/evidence_packet_templates/tajika_steve_jobs_1984_first_packet.json`

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
python3 scripts/tajika_annual_oracle_queue.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --apply-packet references/oracle/evidence_packet_templates/tajika_steve_jobs_1984_first_packet.json --format json
```

## Validate

```bash
python3 scripts/tajika_annual_oracle_queue.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --format json && python3 scripts/tajika_annual_benchmark_dashboard.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --format json
```

## Boundary

This assistant only reports what to fill. It must not invent external oracle values, must not use local engine output as evidence, and must not copy incompatible external code.
