# Ephemeris Adapter Contract - 2026-06-23

Purpose: define the real engineering gate before `xalen_ephemeris`, `vedastro`, or any other `candidate_backend` can become a selectable runtime ephemeris source.

## Contract

The executable contract lives in:

```bash
python3 scripts/ephemeris_adapter_contract.py
```

It defines `EphemerisAdapterContract`, `PARITY_CASES`, and JSON output fields that every backend must satisfy:

- input fields: UTC-adjusted birth date/time, latitude, longitude, timezone, `ayanamsa_policy`, `node_policy`, and `body_list`
- output fields: sidereal longitude, sign, degree in sign, speed, `retrograde`, nakshatra metadata when available, `ayanamsa_value`, backend name, and source metadata
- baseline: `swisseph_python`
- candidate slot: `candidate_backend`

## acceptance_thresholds

The first parity gate is `sun_moon_asc_nodes`:

| Body | Max `longitude_delta_arcsec` |
|---|---:|
| Sun | 1.0 |
| Moon | 1.0 |
| Ascendant | 5.0 |
| Rahu | 2.0 |
| Ketu | 2.0 |

These thresholds are strict enough to catch accidental tropical/sidereal, timezone, node, and ayanamsa mismatches, while leaving a small practical tolerance for backend representation differences.

## Parity Matrix

Current `PARITY_CASES`:

| Case | Why it exists |
|---|---|
| `beijing_first_use_demo` | Reuses the first-use demo chart so product smoke and ephemeris smoke share a reference |
| `delhi_lagna_boundary` | Guards Ascendant, Lahiri ayanamsa, timezone, and mean-node behavior in an India-centered case |
| `new_york_moon_boundary` | Guards western timezone conversion and Moon/nakshatra boundary behavior |

Current decision:

- `swisseph_python` remains the production baseline.
- `swisseph_wasm` remains the browser fallback and can later be compared through the same matrix.
- `xalen_ephemeris` remains `spike_only` until a local adapter can produce this exact contract.
- `vedastro` remains a product/API benchmark unless used behind a service boundary that emits this contract.
- `pyjhora_benchmark` remains AGPL benchmark-only and should provide oracle expected values, not copied implementation code.
