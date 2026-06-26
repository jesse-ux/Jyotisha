# First Dasha Oracle Packet Operator Card

Goal: fill one external Dasha value for `template_steve_jobs_dasha_lahiri`.

do not fill Shadbala in this pass. Shadbala has its own closure board and must not block the first Dasha oracle sample.

## Birth Data

- Date: `1955-02-24`
- Time: `19:15:00`
- Place: San Francisco, CA
- Coordinates: `37.7749, -122.4194`
- Timezone: `UTC-08:00`
- Ayanamsa: `Lahiri`
- Node mode: `true node`

## External Tool

Use one external black-box source:

- JHora Vimshottari Dasha screen, or
- PyJHora black-box output, or
- a documented printed/software example.

Do not use this repository's local engine output as evidence.

## Fill This Packet

Template:

`references/oracle/evidence_packet_templates/dasha_steve_jobs_lahiri_first_packet_only.json`

Required fields:

- `status`: set to `external_verified`
- `metadata.tool_name`
- `metadata.tool_version_or_url`
- `metadata.capture_date`
- `metadata.source_artifact`
- `metadata.operator_note`
- `target.vimshottari_start_date`

Save the redacted screenshot or stdout snippet under `references/oracle/artifacts/`.

## Apply

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --apply-packet references/oracle/evidence_packet_templates/dasha_steve_jobs_lahiri_first_packet_only.json \
  --format json
```

## Validate

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_filled.json

python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_filled.json
```

Expected first milestone after real external evidence is filled:

- Dasha closure board moves from `external_verified_dasha_tasks: 0` to at least `1`.
- Master dashboard still keeps `can_claim_global_oracle_closure: false` until all external oracle fronts are complete.
