# Shadbala External Absolute-Value Closure Status

- shadbala_task_count: `4`
- external_verified_shadbala_tasks: `0`
- can_claim_shadbala_absolute_closure: `false`
- production_tuning_allowed: `false`

## First Priority Packet

- case_id: `template_redacted_place_shadbala_raman`
- capture_id: `external_template_redacted_place_shadbala_raman`
- packet_path: `references/oracle/artifacts/pending_packets/external_template_redacted_place_shadbala_raman.json`
- required_target_fields: `target.moon_sidereal_longitude_deg, target.shadbala_components`
- reject_global_scaling: `true`

## Missing Summary

- metadata: `5`
- target: `50`
- bodies:

  - Jupiter: `7`
  - Mars: `7`
  - Mercury: `7`
  - Moon: `7`
  - Saturn: `7`
  - Sun: `7`
  - Venus: `7`

## Prefilled Fields

- status: `draft`
- promotion_status_after_fill: `external_verified`

- metadata:

  - ayanamsa: `Raman`
  - node_mode: `mean node`
  - timezone: `UTC+08:00`

- settings:

  - ayanamsa: `raman`
  - node_mode: `mean`

## Manual Fill Plan

- status_value: `external_verified`
- manual_entry_count: `55`

## Missing Fields

- `metadata.tool_name`
- `metadata.tool_version_or_url`
- `metadata.capture_date`
- `metadata.operator_note`
- `metadata.source_artifact`
- `target.moon_sidereal_longitude_deg`
- `target.shadbala_components.Sun.sthana`
- `target.shadbala_components.Sun.dig`
- `target.shadbala_components.Sun.kala`
- `target.shadbala_components.Sun.chesta`
- `target.shadbala_components.Sun.naisargika`
- `target.shadbala_components.Sun.drik`
- `target.shadbala_components.Sun.total_rupa`
- `target.shadbala_components.Moon.sthana`
- `target.shadbala_components.Moon.dig`
- `target.shadbala_components.Moon.kala`
- `target.shadbala_components.Moon.chesta`
- `target.shadbala_components.Moon.naisargika`
- `target.shadbala_components.Moon.drik`
- `target.shadbala_components.Moon.total_rupa`
- `target.shadbala_components.Mars.sthana`
- `target.shadbala_components.Mars.dig`
- `target.shadbala_components.Mars.kala`
- `target.shadbala_components.Mars.chesta`
- `target.shadbala_components.Mars.naisargika`
- `target.shadbala_components.Mars.drik`
- `target.shadbala_components.Mars.total_rupa`
- `target.shadbala_components.Mercury.sthana`
- `target.shadbala_components.Mercury.dig`
- `target.shadbala_components.Mercury.kala`
- `target.shadbala_components.Mercury.chesta`
- `target.shadbala_components.Mercury.naisargika`
- `target.shadbala_components.Mercury.drik`
- `target.shadbala_components.Mercury.total_rupa`
- `target.shadbala_components.Jupiter.sthana`
- `target.shadbala_components.Jupiter.dig`
- `target.shadbala_components.Jupiter.kala`
- `target.shadbala_components.Jupiter.chesta`
- `target.shadbala_components.Jupiter.naisargika`
- `target.shadbala_components.Jupiter.drik`
- `target.shadbala_components.Jupiter.total_rupa`
- `target.shadbala_components.Venus.sthana`
- `target.shadbala_components.Venus.dig`
- `target.shadbala_components.Venus.kala`
- `target.shadbala_components.Venus.chesta`
- `target.shadbala_components.Venus.naisargika`
- `target.shadbala_components.Venus.drik`
- `target.shadbala_components.Venus.total_rupa`
- `target.shadbala_components.Saturn.sthana`
- `target.shadbala_components.Saturn.dig`
- `target.shadbala_components.Saturn.kala`
- `target.shadbala_components.Saturn.chesta`
- `target.shadbala_components.Saturn.naisargika`
- `target.shadbala_components.Saturn.drik`
- `target.shadbala_components.Saturn.total_rupa`
## Required Matrix

- planets: `Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn`
- components: `sthana, dig, kala, chesta, naisargika, drik, total_rupa`

## Commands

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --apply-packet references/oracle/artifacts/pending_packets/external_template_redacted_place_shadbala_raman.json --format json
```

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format json > /tmp/jyotish_oracle_queue_filled.json && python3 scripts/oracle_evidence_validator.py --queue-file /tmp/jyotish_oracle_queue_filled.json
```

## Next Actions

- Fill any supporting target fields on the same oracle row, such as Moon sidereal longitude, before validator review.
- Fill all seven planets with Sthana, Dig, Kala, Chesta, Naisargika, Drik and total_rupa from an external oracle.
- Do not use a single global multiplier to force totals; validator checks component sums.
- Set status to external_verified only after artifact path and all Shadbala targets are filled.
- Apply the packet, regenerate the queue, and run oracle_evidence_validator.py.

## Boundary

This board isolates Shadbala absolute values. Dasha boundary dates are a separate closure task. Production tuning remains forbidden until external component-level evidence is complete.
