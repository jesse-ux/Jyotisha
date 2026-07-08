# First Shadbala Absolute-Value Oracle Packet Operator Card

Goal: fill one external Shadbala absolute-value component matrix for `template_synthetic_north_china_shadbala_raman`.

This is for Shadbala only. Do not use Dasha dates, Tajika annual values, or this repository's local Shadbala output as evidence.

## Birth Data

- Date: `1980-01-01`
- Time: `12:00:00`
- Coordinates: `37.7749, -122.4194`
- Timezone: `UTC+08:00`
- Ayanamsa: `Raman`
- Node mode: `mean node`

## External Tool

Use one external black-box source:

- JHora Shadbala component table screenshot, or
- PyJHora black-box Shadbala output, or
- a documented printed/software Shadbala example.

Do not use a global multiplier. The validator expects each planet's `total_rupa` to match the sum of `sthana + dig + kala + chesta + naisargika + drik`.

## Fill This Packet

Template:

`references/oracle/evidence_packet_templates/shadbala_synthetic_north_china_raman_first_packet.json`

Required metadata:

- `status`: set to `external_verified`
- `metadata.tool_name`
- `metadata.tool_version_or_url`
- `metadata.capture_date`
- `metadata.source_artifact`
- `metadata.operator_note`

Supporting target field on the same oracle row:

- `target.moon_sidereal_longitude_deg`

Required Shadbala matrix:

| Planet | Sthana | Dig | Kala | Chesta | Naisargika | Drik | Total Rupa |
|---|---|---|---|---|---|---|---|
| Sun | `target.shadbala_components.Sun.sthana` | `target.shadbala_components.Sun.dig` | `target.shadbala_components.Sun.kala` | `target.shadbala_components.Sun.chesta` | `target.shadbala_components.Sun.naisargika` | `target.shadbala_components.Sun.drik` | `target.shadbala_components.Sun.total_rupa` |
| Moon | `target.shadbala_components.Moon.sthana` | `target.shadbala_components.Moon.dig` | `target.shadbala_components.Moon.kala` | `target.shadbala_components.Moon.chesta` | `target.shadbala_components.Moon.naisargika` | `target.shadbala_components.Moon.drik` | `target.shadbala_components.Moon.total_rupa` |
| Mars | `target.shadbala_components.Mars.sthana` | `target.shadbala_components.Mars.dig` | `target.shadbala_components.Mars.kala` | `target.shadbala_components.Mars.chesta` | `target.shadbala_components.Mars.naisargika` | `target.shadbala_components.Mars.drik` | `target.shadbala_components.Mars.total_rupa` |
| Mercury | `target.shadbala_components.Mercury.sthana` | `target.shadbala_components.Mercury.dig` | `target.shadbala_components.Mercury.kala` | `target.shadbala_components.Mercury.chesta` | `target.shadbala_components.Mercury.naisargika` | `target.shadbala_components.Mercury.drik` | `target.shadbala_components.Mercury.total_rupa` |
| Jupiter | `target.shadbala_components.Jupiter.sthana` | `target.shadbala_components.Jupiter.dig` | `target.shadbala_components.Jupiter.kala` | `target.shadbala_components.Jupiter.chesta` | `target.shadbala_components.Jupiter.naisargika` | `target.shadbala_components.Jupiter.drik` | `target.shadbala_components.Jupiter.total_rupa` |
| Venus | `target.shadbala_components.Venus.sthana` | `target.shadbala_components.Venus.dig` | `target.shadbala_components.Venus.kala` | `target.shadbala_components.Venus.chesta` | `target.shadbala_components.Venus.naisargika` | `target.shadbala_components.Venus.drik` | `target.shadbala_components.Venus.total_rupa` |
| Saturn | `target.shadbala_components.Saturn.sthana` | `target.shadbala_components.Saturn.dig` | `target.shadbala_components.Saturn.kala` | `target.shadbala_components.Saturn.chesta` | `target.shadbala_components.Saturn.naisargika` | `target.shadbala_components.Saturn.drik` | `target.shadbala_components.Saturn.total_rupa` |

Save the redacted screenshot or stdout snippet under `references/oracle/artifacts/`.

## Screen Checklist

Capture only what is needed:

1. Settings screen: Raman ayanamsa, mean node, timezone and location.
2. Moon sidereal longitude screen in absolute 0-360 degree format.
3. Shadbala component table showing all seven planets.
4. A note showing whether values are Rupa or Virupa.
5. If the tool shows Virupa only, record the unit in `operator_note` before converting or leave values unconverted and state that clearly for review.

## Apply

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --apply-packet references/oracle/evidence_packet_templates/shadbala_synthetic_north_china_raman_first_packet.json \
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

- Shadbala closure board moves from `external_verified_shadbala_tasks: 0` to at least `1`.
- `reject_global_scaling` remains true.
- Master dashboard still keeps `can_claim_global_oracle_closure: false` until all external oracle fronts are complete.
