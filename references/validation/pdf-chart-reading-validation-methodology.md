# PDF Chart Reading Validation Methodology

> Version: v6.1.9-public-methodology
> Purpose: Convert private PDF-chart validation experience into a reusable, privacy-safe quality gate.
> Privacy boundary: This document intentionally excludes personal birth data, exact chart degrees, life events, raw PDF text, and private full-reading JSON.

## 1. When to use this protocol

Use this protocol when the input is a PDF, screenshot, or text export from astrology software rather than raw birth data.

Typical sources:

- Jagannatha Hora / Parashara's Light PDF export
- Screenshot or OCR of a Vedic chart
- User-provided text listing D1/D9/Dasha tables
- Mixed PDF containing chart pages, strength tables, and divisional charts

## 2. Validation principle

A PDF chart is not automatically trustworthy as machine-readable data. Treat it as a source document that must pass layered checks before interpretation.

Validation layers:

1. Source extraction: obtain all visible text and page structure.
2. Identity lock: confirm date, time, timezone, place, ayanamsa, node mode, and chart style.
3. Core chart lock: confirm D1 ascendant, Moon sign/nakshatra, Rahu/Ketu axis, and visible house layout.
4. Dasha lock: confirm Mahadasha/Antardasha sequence and current period.
5. Strength lock: confirm Ashtakavarga/Shadbala/Vimsopaka tables if present.
6. Engine recomputation: run `full-reading` from extracted birth data.
7. Difference arbitration: explicitly separate PDF-origin facts, engine-recomputed facts, and unresolved differences.
8. Interpretation boundary: only use A/B confidence for claims that passed the relevant gate.

## 3. Minimum quality gate

A PDF input may proceed to interpretation only if these fields are available and internally consistent:

| Gate | Required fields | Pass condition |
|---|---|---|
| Birth data | Date, local time, timezone, place | No contradiction between PDF pages |
| D1 core | Ascendant, Moon sign, Rahu/Ketu axis | PDF and recomputed engine agree or difference is explained |
| D9 core | Navamsa ascendant or full D9 table | Available from PDF or recomputation |
| Dasha | Current Mahadasha and Antardasha | Period sequence matches Vimshottari calculation within expected boundary tolerance |
| Node mode | Mean/True node | Explicitly stated or inferred and documented |
| Ayanamsa | Lahiri/other | Explicitly stated or inferred and documented |

If any gate fails, downgrade the reading and state the uncertainty.

## 4. Recommended extraction workflow

1. Extract text from every page.
2. Record page-level coverage: which pages contain D1, D9, Dasha, strength tables, transit tables, or divisional charts.
3. Normalize names: map software-specific labels to engine fields.
4. Recompute with `scripts/jyotish_engine.py full-reading`.
5. Compare the following high-impact fields first:
   - Ascendant sign
   - Moon sign and nakshatra
   - Rahu/Ketu signs and node mode
   - Current Vimshottari Mahadasha/Antardasha
   - D9 ascendant and key dignity states
   - SAV total and house scores if Ashtakavarga is present
   - Shadbala ranking if a strength table is present
6. Create a discrepancy table before interpreting.

## 5. Confidence levels

| Level | Meaning | Allowed usage |
|---|---|---|
| A | PDF and engine agree, or discrepancy has authoritative explanation | Can support direct interpretation |
| B | One strong source plus secondary partial confirmation | Can support cautious interpretation |
| C | Single source, OCR uncertain, or chart-image page not fully parsed | Use only as a hypothesis |
| D | Contradicted or missing | Do not use for prediction |

## 6. Common downgrade triggers

- PDF text extraction cannot reconstruct chart grid positions.
- Divisional chart pages appear as images or broken table text.
- Dasha period boundary differs due to timezone or ayanamsa assumptions.
- Rahu/Ketu mismatch is caused by Mean Node vs True Node.
- Shadbala values are from a different software formula or ayanamsa.
- OCR confuses signs, degrees, or retrograde markers.

## 7. Discrepancy table template

| Field | PDF value | Engine value | Status | Action |
|---|---|---|---|---|
| Birth date/time/place |  |  | A/B/C/D |  |
| Ayanamsa |  |  | A/B/C/D |  |
| Node mode |  |  | A/B/C/D |  |
| D1 ascendant |  |  | A/B/C/D |  |
| Moon sign/nakshatra |  |  | A/B/C/D |  |
| Rahu/Ketu axis |  |  | A/B/C/D |  |
| Current MD/AD |  |  | A/B/C/D |  |
| D9 ascendant |  |  | A/B/C/D |  |
| SAV total |  |  | A/B/C/D |  |
| Shadbala ranking |  |  | A/B/C/D |  |

## 8. Privacy rule

Never commit private PDF extracts, exact private birth data, private life-event validation, or raw full-reading JSON generated from a user chart to the public repository. If a workflow lesson is useful, extract only the generic method and remove identifying details.

## 9. Output requirement

When using a PDF chart in a reading, the final report must include:

1. Source type: PDF/OCR/text export.
2. Quality gate summary.
3. Which fields are A/B/C/D.
4. Which claims rely on PDF facts vs engine recomputation.
5. Explicit caveats for any chart-image or OCR-only sections.
