# First Oracle Packet Assistant Index

Generated: `2026-07-01T17:18:16.817728+00:00`

## Fronts

| front | case_id | missing fields | ready_to_apply |
|---|---|---:|---|
| `dasha` | `template_steve_jobs_dasha_lahiri` | 0 | `true` |
| `tajika_sahams` | `template_einstein_varshaphala_1905_lahiri` | 0 | `true` |
| `shadbala` | `template_synthetic_north_china_shadbala_raman` | 0 | `true` |

## Recommended Order

### dasha

- case_id: `template_steve_jobs_dasha_lahiri`
- missing_field_count: `0`
- operator_card: `docs/benchmark/dasha_steve_jobs_first_packet_operator_card.md`

```bash

```

### tajika_sahams

- case_id: `template_einstein_varshaphala_1905_lahiri`
- missing_field_count: `0`
- operator_card: `docs/benchmark/tajika_einstein_1905_first_packet_operator_card.md`

```bash
python3 scripts/tajika_annual_oracle_queue.py --oracle-file references/oracle/tajika_annual_oracle_cases.json --apply-packet references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json --format json
```

### shadbala

- case_id: `template_synthetic_north_china_shadbala_raman`
- missing_field_count: `0`
- operator_card: `docs/benchmark/shadbala_synthetic_north_china_raman_first_packet_operator_card.md`

```bash

```

## Boundary

This index aggregates packet assistants only. It does not create oracle values, does not validate packets by itself, and does not change oracle files.
