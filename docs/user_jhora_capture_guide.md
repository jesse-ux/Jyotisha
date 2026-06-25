# JHora/PyJHora External Evidence Capture Guide

This guide turns the first Dasha/Shadbala oracle sample from a draft into a
reviewable external evidence packet. It is for manual black-box capture only:
do not copy JHora/PyJHora implementation code, formulas, constants, or private
reports into this repository.

## Safe Case Choice

Start with one of these public or synthetic tasks:

- `template_steve_jobs_dasha_lahiri`: public-figure Dasha boundary sample.
- `template_user_REDACTED_YEAR_moon_longitude_lahiri`: user-template sample; use only if
  the screenshot is heavily redacted.

Avoid private client material for the first pass. If a private screenshot is
unavoidable, it 必须打码 before it enters `references/oracle/artifacts/`.

## Privacy Rules

- Store evidence only under `references/oracle/artifacts/`.
- `source_artifact` must be a repo-relative path such as
  `references/oracle/artifacts/jhora_steve_jobs_dasha_lahiri_v1.png`.
- 必须打码 names, addresses, account names, notifications, file paths, browser
  tabs, and any personally identifying text.
- 不得提交私人 PDF 原件.
- 不得提交完整出生报告.
- 不得提交浏览器 scratch folders, cookies, account sessions, tokens, desktop
  notifications, or downloaded temp folders.

## External Tool Setup

For JHora:

1. Open a clean chart in JHora.
2. Enter the exact date, time, timezone, latitude, and longitude from
   `references/oracle/dasha_shadbala_oracle_cases.json`.
3. Set ayanamsa explicitly. The first pass should use Lahiri; later samples
   should repeat with Raman and KP.
4. Record whether the tool is using mean node or true node. The packet metadata
   must write this exactly as `mean node` or `true node`.
5. Keep the tool version, build date, or download URL visible in notes if
   possible.

For PyJHora:

1. Use an isolated environment and treat output as a black-box external
   reference.
2. Record the package version and command or script path in operator notes.
3. Capture stdout as a text artifact only if it contains the requested target
   values and no private data.
4. Because PyJHora license metadata can vary by source, use it as an external
   behavior oracle unless a separate license review approves direct reuse.

## Required Screenshots Or Stdout

Capture enough external evidence to fill every requested target field.

### Moon sidereal longitude

Required for `template_user_REDACTED_YEAR_moon_longitude_lahiri`.

- Capture Moon sidereal longitude in absolute 0-360 degrees if available.
- Also capture sign-local degrees/minutes/seconds when the tool shows it.
- Record ayanamsa, timezone, and node mode beside the value.

### Vimshottari start date

Required for `template_user_REDACTED_YEAR_moon_longitude_lahiri`,
`template_steve_jobs_dasha_lahiri`, and
`template_historical_epoch_lahiri`.

- Capture the Vimshottari start date or first Mahadasha boundary shown by the
  external tool.
- Write it as ISO date in `target.vimshottari_start_date`, for example
  `1986-05-18`.
- If the tool uses a visible year length, DST, or local sunrise policy, record
  that in `operator_note`.

### Shadbala 七曜六分量

Required for every task whose target includes `shadbala_components`.

The packet must include all seven planets:

- Sun
- Moon
- Mars
- Mercury
- Jupiter
- Venus
- Saturn

Each planet must include all six components:

- `sthana`
- `dig`
- `kala`
- `chesta`
- `naisargika`
- `drik`

Do not fill only a total. Do not apply a global scaling factor. If the tool
shows Rupa and Virupa, record the unit in `operator_note` and preserve the
component numbers exactly as read from the screenshot or stdout.

## Artifact Naming

Use short, stable names:

- `references/oracle/artifacts/jhora_steve_jobs_lahiri_dasha_v1.png`
- `references/oracle/artifacts/jhora_steve_jobs_lahiri_shadbala_v1.png`
- `references/oracle/artifacts/pyjhora_steve_jobs_lahiri_stdout_v1.txt`
- `references/oracle/artifacts/jhora_user_REDACTED_YEAR_lahiri_redacted_v1.png`

If a screenshot is corrected, keep the old artifact only if it is already
referenced by a packet; otherwise replace the draft before review.

## Packet Fill Procedure

Generate the current queue:

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_capture.json
```

Choose the task matching the external tool output, then fill:

- `evidence_packet.status`: `external_verified`
- `evidence_packet.metadata.tool_name`: `JHora` or `PyJHora`
- `evidence_packet.metadata.tool_version_or_url`
- `evidence_packet.metadata.capture_date`
- `evidence_packet.metadata.source_artifact`
- `evidence_packet.metadata.ayanamsa`: `Lahiri`, `Raman`, or `KP`
- `evidence_packet.metadata.node_mode`: `mean node` or `true node`
- `evidence_packet.metadata.timezone`
- `evidence_packet.metadata.operator_note`
- `evidence_packet.target_placeholders.target.moon_sidereal_longitude_deg`
- `evidence_packet.target_placeholders.target.vimshottari_start_date`
- `evidence_packet.target_placeholders.target.shadbala_components`

For a valid first Shadbala row, the component object must look like this shape:

```json
{
  "Sun": {"sthana": 0, "dig": 0, "kala": 0, "chesta": 0, "naisargika": 0, "drik": 0},
  "Moon": {"sthana": 0, "dig": 0, "kala": 0, "chesta": 0, "naisargika": 0, "drik": 0},
  "Mars": {"sthana": 0, "dig": 0, "kala": 0, "chesta": 0, "naisargika": 0, "drik": 0},
  "Mercury": {"sthana": 0, "dig": 0, "kala": 0, "chesta": 0, "naisargika": 0, "drik": 0},
  "Jupiter": {"sthana": 0, "dig": 0, "kala": 0, "chesta": 0, "naisargika": 0, "drik": 0},
  "Venus": {"sthana": 0, "dig": 0, "kala": 0, "chesta": 0, "naisargika": 0, "drik": 0},
  "Saturn": {"sthana": 0, "dig": 0, "kala": 0, "chesta": 0, "naisargika": 0, "drik": 0}
}
```

Replace every `0` with the external value. A zero is valid only if the external
tool literally shows zero.

## Validation

Run the validator against the filled queue:

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_capture.json
```

The first successful sample should move the summary from `valid_packets: 0` to
`valid_packets: 1`, and from `ready_for_calibration: 0` to
`ready_for_calibration: 1`. This does not allow production tuning by itself; it
only means one packet is review-ready.

## Reject And Recapture Cases

Reject the packet and recapture if any of these occur:

- `missing_external_artifact`
- `status_not_external_verified:draft`
- `local_engine_artifact_rejected`
- `missing_shadbala_component:all_planets`
- `missing_shadbala_component:Sun.kala` or any other component-level error
- Screenshot does not show ayanamsa.
- Screenshot does not show whether mean node or true node was used.
- Source artifact contains unredacted private data.
- Source artifact is a private PDF original or complete birth report.
- Values came from this repository's local engine instead of JHora/PyJHora or
  another external oracle.

## Minimal Recapture Checklist

If the screenshot is not enough, recapture only the missing evidence:

1. Tool/version and settings screen.
2. Moon sidereal longitude screen.
3. Vimshottari start date screen.
4. Shadbala component table with all seven planets and six components.
5. A short operator note explaining ayanamsa, node mode, timezone, and unit.
