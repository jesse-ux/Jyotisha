# First External Oracle Packet Assistant

- front: `shadbala`
- case_id: `template_redacted_place_shadbala_raman`
- capture_id: `external_template_redacted_place_shadbala_raman`
- ready_to_apply: `false`
- operator_card: `docs/benchmark/shadbala_redacted_place_raman_first_packet_operator_card.md`
- packet_template: `references/oracle/evidence_packet_templates/shadbala_redacted_place_raman_first_packet.json`

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

## External Sources

- JHora Shadbala component table screenshot
- PyJHora black-box shadbala output
- documented printed/software Shadbala example

## Apply

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --apply-packet references/oracle/evidence_packet_templates/shadbala_redacted_place_raman_first_packet.json --format json
```

## Validate

```bash
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format json > /tmp/jyotish_oracle_queue_filled.json && python3 scripts/oracle_evidence_validator.py --queue-file /tmp/jyotish_oracle_queue_filled.json
```

## Boundary

This assistant only reports what to fill. It must not invent external oracle values, must not use local engine output as evidence, and must not copy incompatible external code.
