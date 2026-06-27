# Tajika Einstein 1905 Fill Map

Packet: `template_einstein_varshaphala_1905_lahiri`  
Apply target: `references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json`

This map exists to reduce guesswork while filling the next Tajika / Sahams annual external oracle packet.

Record the exact solar-return convention in `metadata.operator_note`, especially timezone/DST handling and whether the tool computes the annual chart at exact solar return.

## Metadata

| Field | What to write | Source |
|---|---|---|
| `metadata.tool_name` | `JHora`, `PyJHora`, or book/source name | The external tool or book you used |
| `metadata.tool_version_or_url` | Version string, release tag, or bibliographic pointer | Tool about dialog, stdout header, or citation |
| `metadata.capture_date` | Date of capture in `YYYY-MM-DD` | The day you captured the evidence |
| `metadata.source_artifact` | Repo-relative file under `references/oracle/artifacts/` | Redacted screenshot, stdout snippet, or citation note |
| `metadata.operator_note` | A short note about ayanamsa, node mode, timezone, and solar-return convention | Your own note from the run |

## Annual Targets

| Field | What to copy | Preferred place to read it |
|---|---|---|
| `target.solar_return_datetime` | Exact solar return timestamp with offset if shown | JHora annual chart header, PyJHora annual output header, or printed example note |
| `target.varsha_lagna_deg` | Varsha Lagna degree in absolute zodiac degrees | Annual chart ascendant line or annual report table |
| `target.muntha_sign` | Muntha sign name | Muntha section in the annual chart report |
| `target.year_lord` | Year Lord name | Year Lord / Varshesha section |
| `target.mudda_dasha_first_lord` | First Mudda Dasha lord | Mudda Dasha table, first row |
| `target.sahams.punya_saham` | Punya Saham absolute degree | Sahams table |
| `target.sahams.rajya_saham` | Rajya Saham absolute degree | Sahams table |
| `target.sahams.vivah_saham` | Vivah Saham absolute degree | Sahams table |
| `target.tajika_yogas` | Visible yoga structure exactly as the external source presents it | Tajika Yogas screen or stdout block |
| `target.source_artifact` | Same artifact path or a more specific annual proof file | Same evidence set as `metadata.source_artifact` |

## Screen Checklist

Use one external source only per pass:

1. `JHora` Varshaphala/Tajika annual chart screen, or
2. `PyJHora` black-box annual output, or
3. one printed Tajika/Varshaphala example.

Capture only what is needed:

1. Settings screen: ayanamsa, node mode, location, target year, solar-return convention.
2. Annual chart header: solar return datetime.
3. Annual ascendant / Varsha Lagna line.
4. Muntha / Year Lord section.
5. Mudda Dasha section.
6. Sahams section.
7. Tajika Yogas section.

## Boundary

- Do not use local `scripts/varshaphala.py` output as evidence.
- Do not mix multiple tools into one single packet unless `metadata.operator_note` explicitly documents it.
- Keep `target.tajika_yogas` faithful to the external source labels rather than translating them through local interpretation logic.
