# Western Oracle Adapter Contract

This contract defines how external Western astrology outputs enter the high-rigor Jyotish workflow.

## Purpose

`scripts/western_oracle_adapter.py` converts an external Western astrology JSON export into the standard `western_evidence_packet`.

It is an evidence adapter, not a bundled Western astrology engine.

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
