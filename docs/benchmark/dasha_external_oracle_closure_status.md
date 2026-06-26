# Dasha External Oracle Closure Status

- dasha_task_count: `3`
- external_verified_dasha_tasks: `0`
- can_claim_dasha_oracle_closure: `false`
- production_tuning_allowed: `false`

## First Priority Packet

- case_id: `template_steve_jobs_dasha_lahiri`
- capture_id: `external_template_steve_jobs_dasha_lahiri`
- packet_path: `references/oracle/artifacts/pending_packets/external_template_steve_jobs_dasha_lahiri.json`
- required_target_fields: `target.vimshottari_start_date`

## Missing Summary

- metadata: `5`
- target: `1`

## Prefilled Fields

- status: `draft`
- promotion_status_after_fill: `external_verified`

- metadata:

  - ayanamsa: `Lahiri`
  - node_mode: `true node`
  - timezone: `UTC-08:00`

- settings:

  - ayanamsa: `lahiri`
  - node_mode: `true`

## Manual Fill Plan

- status_value: `external_verified`
- manual_entry_count: `6`

## Missing Fields

- `metadata.tool_name`
- `metadata.tool_version_or_url`
- `metadata.capture_date`
- `metadata.operator_note`
- `metadata.source_artifact`
- `target.vimshottari_start_date`
## Commands

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --apply-packet references/oracle/artifacts/pending_packets/external_template_steve_jobs_dasha_lahiri.json --format json
```

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format json > /tmp/jyotish_oracle_queue_filled.json && python3 scripts/oracle_evidence_validator.py --queue-file /tmp/jyotish_oracle_queue_filled.json
```

## Next Actions

- Open the first priority packet and fill metadata from an external oracle.
- Fill target.vimshottari_start_date only from JHora/PyJHora/book example, not from this repository.
- Set status to external_verified after the artifact path and Dasha target are filled.
- Apply the packet, regenerate the queue, and run oracle_evidence_validator.py.

## Boundary

This board isolates the Dasha shortest path. Shadbala remains a separate absolute-value closure task and must not block collecting the first Dasha boundary date.
