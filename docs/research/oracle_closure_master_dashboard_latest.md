# Jyotish External Oracle Closure Master Dashboard

Generated: `2026-06-26T18:24:45.835960+00:00`

## Summary

- total_tasks: `12`
- external_verified_tasks: `6`
- open_tasks: `6`
- can_claim_global_oracle_closure: `false`
- production_tuning_allowed: `false`

## Fronts

| front | tasks | verified | first priority | missing fields | manual entries | metadata missing | target missing |
|---|---:|---:|---|---:|---:|---:|---:|
| `dasha` | 3 | 3 | `complete` | 0 | 0 | 0 | 0 |
| `tajika_sahams` | 5 | 0 | `template_steve_jobs_varshaphala_1984_lahiri` | 15 | 15 | 5 | 10 |
| `shadbala` | 4 | 3 | `template_extreme_latitude_kp` | 54 | 54 | 5 | 49 |

## Next Action Order

### tajika_sahams

- case_id: `template_steve_jobs_varshaphala_1984_lahiri`
- capture_id: `external_template_steve_jobs_varshaphala_1984_lahiri`
- missing_field_count: `15`
- manual_entry_count: `15`

```bash
python3 scripts/tajika_annual_oracle_queue.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --apply-packet references/oracle/artifacts/pending_packets/external_template_steve_jobs_varshaphala_1984_lahiri.json --format json
```

### shadbala

- case_id: `template_extreme_latitude_kp`
- capture_id: `external_template_extreme_latitude_kp`
- missing_field_count: `54`
- manual_entry_count: `54`

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --apply-packet references/oracle/artifacts/pending_packets/external_template_extreme_latitude_kp.json --format json
```

## Boundary

This dashboard merges external evidence readiness only. It does not claim prediction accuracy, does not tune production constants, and does not treat local engine output as oracle evidence.
