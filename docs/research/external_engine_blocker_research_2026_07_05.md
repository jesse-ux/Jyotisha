# External Engine Blocker Research 2026-07-05

Purpose: record what can be fixed locally vs. what remains blocked by external engines, licensing, or credentials.

## PyJHora / JHora

- PyPI package checked: `PyJHora`
- Observed PyPI version: `4.8.7`
- Upstream GitHub search top match: `naturalstupid/PyJHora`
- Observed GitHub license: `AGPL-3.0`
- Local status: `scripts/diagnose_pyjhora_adapter.py --json` reports `missing_dependency: jhora`
- Local action now implemented: diagnostics expose install hint, ephemeris-data note, and AGPL boundary.

Boundary:

- Do not vendor PyJHora into this repo.
- Do not make PyJHora a required runtime dependency.
- Keep it as optional external benchmark / parity oracle.

Install hint for a separate benchmark environment:

```bash
pip install PyJHora
```

## VedAstro

- Public site checked: `https://vedastro.org/` returned reachable.
- `https://api.vedastro.org/api` returned HTTP 404 for a direct root probe. This only proves host reachability; it does not prove a full-snapshot endpoint is configured.
- Current local diagnostic: `scripts/diagnose_external_engine_adapters.py --json` reports VedAstro `available` in `official_extended` mode but with `premium_key_missing`.

Closure rule:

- Do not claim VedAstro cloud closure unless `vedastro_official.raw_response` is present in the runtime evidence packet.
- Free tier can remain `blocked` or `partial`; API key is recommended for stable official full snapshot.

## Current Aggregate Status

- VedAstro: `available`, blocker `premium_key_missing`
- PyJHora/JHora: `missing_dependency`, blocker `jhora`
- jyotishganit: `available`, license `MIT`
- Three-engine parity: `partial`, not complete.

## Sources Checked

- PyPI: `https://pypi.org/project/PyJHora/`
- GitHub search/API result: `https://github.com/naturalstupid/PyJHora`
- VedAstro site: `https://vedastro.org/`
- VedAstro API host probe: `https://api.vedastro.org/api`
