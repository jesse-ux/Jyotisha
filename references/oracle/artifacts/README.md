# External Oracle Artifacts

This directory stores sanitized evidence artifacts referenced by `source_artifact`
inside external oracle evidence packets.

## Required Path Policy

- Use repo-relative paths such as `references/oracle/artifacts/jhora_REDACTED_YEAR_moon_lahiri_v1.png`.
- `source_artifact` must point to a file in `references/oracle/artifacts/` or to a documented external review location.
- Mark the artifact kind as `external_oracle_artifact` in operator notes when possible.

## Privacy Rules

- 必须打码 any real person's full name, contact details, exact street address, hospital, account name, or other identifying text.
- 不得提交私人 PDF 原件；only sanitized screenshots or typed stdout snippets belong here.
- 不得提交完整出生报告 or full private reading transcripts.
- 不得提交浏览器 scratch folders, screenshots containing account sessions, cookies, tokens, or desktop notifications.
- Prefer synthetic fixtures, public figures, or heavily redacted screenshots.

## Allowed Examples

- Redacted JHora screenshot showing settings, Moon longitude, Dasha boundary, or Shadbala component table.
- Redacted PyJHora stdout captured in a plain text file with command metadata.
- Public-figure sample screenshot where source settings are visible and no private account data appears.

## Not Allowed

- Unredacted volunteer/client birth data.
- `output_report.txt`, `results_extracted.md`, private PDFs, or full generated readings.
- Local engine output from this repository pretending to be an external oracle.

Evidence packets remain `draft` until their target values are filled, their
artifact is reviewed, and their status is explicitly promoted to
`external_verified`.
