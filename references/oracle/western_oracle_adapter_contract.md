# Western Oracle Adapter Contract

This contract defines how external Western astrology outputs enter the high-rigor Jyotish workflow.

## Purpose

`scripts/western_oracle_adapter.py` converts an external Western astrology JSON export into the standard `western_evidence_packet`.

It is an evidence adapter, not a bundled Western astrology engine.

## Native Tropical Natal Layer

`scripts/western_chart_engine.py` uses the existing Swiss Ephemeris binding to
calculate a tropical natal chart from birth data. For `direct_chart` and
`rectification`, the unified workflow defaults to `western_mode: "auto"` when
no external payload is supplied. It records planetary longitude/speed,
Placidus houses, ASC/MC/DC/IC, major aspects with explicit orb limits,
element/mode distribution, and traditional house-ruler chains.

The native result is deliberately `partial`: it does **not** calculate
secondary progressions, solar arcs, non-solar returns, synastry, or
interpretive signals. `prashna` does not receive a natal Western packet by
default. Set `western_mode` to `external_only` or `off` to suppress automatic
calculation. Explicit `western_evidence_packet` and `western_oracle_payload`
always take precedence.

### Optional Timing Input

To add only requested native time evidence, pass:

```json
{
  "western_timing": {
    "transit_date": "2026-07-09",
    "solar_return_year": 2026,
    "secondary_progression_date": "2026-07-09",
    "solar_arc_date": "2026-07-09"
  }
}
```

`transit_date` produces a local-date transit-to-natal major-aspect snapshot.
`solar_return_year` locates the exact tropical solar return and calculates its
return chart at the supplied birthplace/location. Both are calculation data,
not event verdicts. `secondary_progression_date` uses one ephemeris day per
tropical year for progressed planets. `solar_arc_date` applies the true
secondary-progressed-Sun arc to natal planets/ASC/MC. Both remain `partial`:
progressed angles, converses, parans, midpoints, duration, and interpretation
are not asserted.

## Accepted Input

```json
{
  "source_engine": "kerykeion_external_json",
  "natal": {
    "ascendant": "Virgo",
    "mc": "Gemini"
  },
  "timing_techniques": {
    "solar_return": {
      "annual_focus": "career"
    }
  },
  "aspects": [
    {
      "date": "2026-07-07",
      "planet": "Uranus",
      "aspect": "conjunction",
      "target": "MC"
    }
  ]
}
```

Explicit `signals` may be provided. When present, explicit signals are preserved and aspect-derived signals are not guessed.

## Derived Signal Rules

The adapter currently maps only a small auditable subset:

| Aspect Pattern | Signal |
|---|---|
| Uranus conjunction MC/Midheaven | `career_relocation / career_triggered_relocation` |
| Jupiter trine/sextile Mercury/Venus/MC | `career / client_cooperation_opportunity` |
| Saturn conjunction Sun/Mercury/Venus | `career / career_responsibility_test` |

More mappings require tests and source notes before being added.

## Entry Points

API and MCP callers may pass either field:

- `western_oracle_payload`: raw external Western astrology JSON export; the project normalizes it with `western_oracle_adapter`.
- `western_evidence_packet`: pre-normalized packet; the project carries it directly into `runtime_evidence_log`.
- `western_mode`: `auto` (default for non-Prashna birth-chart entries), `external_only`, or `off`.

When Jyotish evidence also carries matching `cross_system_signals`, `Cross-System Arbitration` can become `used`. If only Western evidence is present, arbitration stays `partial` or `blocked`.

## CLI

```bash
python3 scripts/western_oracle_adapter.py \
  --input /path/to/western_oracle.json \
  --theme career \
  --question-type career
```

The command prints a `western_evidence_packet` JSON object.

## License Boundary

The premium skill may accept JSON exports from Kerykeion, Flatlib, Immanuel, Astro.com, GongShenXing, or desktop software.

Do not copy third-party source code into the premium package unless the exact project and dependency licenses permit bundling.

The adapter stores derived evidence and source labels only.
