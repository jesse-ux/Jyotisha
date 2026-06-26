# Tajika/Sahams Annual Closure Status

- annual_task_count: `5`
- external_verified_annual_tasks: `0`
- can_claim_tajika_sahams_closure: `false`
- production_tuning_allowed: `false`

## First Priority Packet

- case_id: `template_steve_jobs_varshaphala_1984_lahiri`
- capture_id: `external_template_steve_jobs_varshaphala_1984_lahiri`
- packet_path: `references/oracle/artifacts/pending_packets/external_template_steve_jobs_varshaphala_1984_lahiri.json`
- required_target_fields: `target.solar_return_datetime, target.varsha_lagna_deg, target.muntha_sign, target.year_lord, target.mudda_dasha_first_lord, target.sahams.punya_saham, target.sahams.rajya_saham, target.sahams.vivah_saham, target.tajika_yogas, target.source_artifact`
- missing_fields: `metadata.tool_name, metadata.tool_version_or_url, metadata.capture_date, metadata.operator_note, metadata.source_artifact, target.solar_return_datetime, target.varsha_lagna_deg, target.muntha_sign, target.year_lord, target.mudda_dasha_first_lord, target.sahams.punya_saham, target.sahams.rajya_saham, target.sahams.vivah_saham, target.tajika_yogas, target.source_artifact`

## Commands

```bash
python3 scripts/tajika_annual_oracle_queue.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --apply-packet references/oracle/artifacts/pending_packets/external_template_steve_jobs_varshaphala_1984_lahiri.json --format json
```

```bash
python3 scripts/tajika_annual_oracle_queue.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --format json && python3 scripts/tajika_annual_benchmark_dashboard.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --format json
```

## Next Actions

- Fill solar return datetime, Varsha Lagna, Muntha, Year Lord, first Mudda Dasha lord, three Sahams and Tajika Yogas from an external annual source.
- Document timezone/DST and solar-return convention before promoting the row.
- Set the row to external_verified only after target.source_artifact and metadata.source_artifact point to reviewable evidence.
- Regenerate the annual queue and benchmark dashboard.

## Boundary

This board isolates Tajika/Sahams annual closure. Local scripts/varshaphala.py output is not an external oracle and must not be used as production tuning evidence.
