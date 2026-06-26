# First External Oracle Packet Assistant

- front: `dasha`
- case_id: `template_steve_jobs_dasha_lahiri`
- capture_id: `external_template_steve_jobs_dasha_lahiri`
- ready_to_apply: `false`
- operator_card: `docs/benchmark/dasha_steve_jobs_first_packet_operator_card.md`
- packet_template: `references/oracle/evidence_packet_templates/dasha_steve_jobs_lahiri_first_packet_only.json`

## Missing Summary

- metadata: `5`
- target: `1`

## Missing Fields

- `metadata.tool_name`
- `metadata.tool_version_or_url`
- `metadata.capture_date`
- `metadata.operator_note`
- `metadata.source_artifact`
- `target.vimshottari_start_date`

## External Sources

- JHora Vimshottari Dasha screen
- PyJHora black-box dasha output
- documented printed/software example

## Apply

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --apply-packet references/oracle/evidence_packet_templates/dasha_steve_jobs_lahiri_first_packet_only.json --format json
```

## Validate

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format json > /tmp/jyotish_oracle_queue_filled.json && python3 scripts/oracle_evidence_validator.py --queue-file /tmp/jyotish_oracle_queue_filled.json
```

## Boundary

This assistant only reports what to fill. It must not invent external oracle values, must not use local engine output as evidence, and must not copy incompatible external code.
