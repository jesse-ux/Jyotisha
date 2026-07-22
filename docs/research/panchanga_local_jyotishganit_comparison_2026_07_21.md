# Panchanga local ↔ jyotishganit comparison — TEMCQ-061

Date: 2026-07-21

This packet closes the first local comparison step for the Panchanga schema ticket without writing a new Panchanga algorithm.

## Result

- Local method: `scripts/muhurta.py::calc_panchanga`
- Case: Steve Jobs
- Compared fields: `vaara`, `tithi`, `nakshatra`, `yoga`, `karana`
- Result: 4 exact matches + 1 naming alias
- Truth upgrade: 0

## Field comparison

| Field | Local | jyotishganit | Status |
|---|---|---|---|
| vaara | Thursday | Thursday | within_tolerance |
| tithi | Shukla Tritiya | Shukla Tritiya | within_tolerance |
| nakshatra | Uttara Bhadrapada | Uttara Bhadrapada | within_tolerance |
| yoga | Shubha | Shubha | within_tolerance |
| karana | Garija | Gara | alias_match |

`Gara` and `Garija` are recorded as a naming alias, not a formula mismatch.

## Boundary

This is still `research_observation_only`. It does not upgrade Panchanga to global truth because VedAstro and PyJHora/JHora five-field normalized packets are not pinned for this same comparison, and sunrise-relative semantics still need multi-case closure.
