# Jyotish External Oracle Closure Master Dashboard

Generated: `2026-06-26T17:25:44.270300+00:00`

## Summary

- total_tasks: `12`
- external_verified_tasks: `4`
- open_tasks: `8`
- can_claim_global_oracle_closure: `false`
- production_tuning_allowed: `false`

## Fronts

| front | tasks | verified | first priority | missing fields | manual entries | metadata missing | target missing |
|---|---:|---:|---|---:|---:|---:|---:|
| `dasha` | 3 | 3 | `complete` | 0 | 0 | 0 | 0 |
| `tajika_sahams` | 5 | 0 | `template_steve_jobs_varshaphala_1984_lahiri` | 15 | 15 | 5 | 10 |
| `shadbala` | 4 | 1 | `template_user_REDACTED_YEAR_moon_longitude_lahiri` | 55 | 55 | 5 | 50 |

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

- case_id: `template_user_REDACTED_YEAR_moon_longitude_lahiri`
- capture_id: `external_template_user_REDACTED_YEAR_moon_longitude_lahiri`
- missing_field_count: `55`
- manual_entry_count: `55`

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --apply-packet references/oracle/artifacts/pending_packets/external_template_user_REDACTED_YEAR_moon_longitude_lahiri.json --format json
```

## Boundary

This dashboard merges external evidence readiness only. It does not claim prediction accuracy, does not tune production constants, and does not treat local engine output as oracle evidence.
