# Jyotishyamitra Pinned Adapter Probe - 2026-07-18

## Status

`jyotishyamitra` is pinned as a fourth independent observation oracle only.

It is not part of the three-engine truth matrix and does not promote any claim.

## Identity

- Package: `jyotishyamitra`
- Version: `1.4.0`
- GitHub commit: `86f7eb610a66b06b3f0817d2c53355bec8b3bf8d`
- License: MIT in wheel license file
- Wheel SHA-256: `4f1a16facfa86ef01cb44de505c6de2e66b2f8d2c8b5e125c090e3f8485c6a9d`
- Python wheel tag: `py3-none-any`
- Requires Python: `>=3.7`

## Execution Boundary

- Adapter: `scripts/jyotishyamitra_adapter_probe.py`
- Tests: `tests/test_jyotishyamitra_adapter_probe.py`
- The wheel is installed with `pip --target` into a temporary directory.
- The package is invoked in an isolated subprocess with temporary `PYTHONPATH`.
- `jyotishyamitra` is not a project runtime dependency and is not imported by commercial runtime code.
- No implementation code is copied from the package.

## Canonical Request

The Steve Jobs probe records:

- birth: `1955-02-24 19:15:00`
- place: `San Francisco, CA`
- longitude: `-122.4194`
- latitude: `37.7749`
- timezone: `-8.0`
- ayanamsa: `package_default`
- node mode: `package_default`
- returnval: `ASTRODATA_DICTIONARY`

## Artifacts

- Metadata-only: `references/oracle/jyotishyamitra_pinned_adapter_probe_2026_07_18.json`
- Steve Jobs execution probe: `references/oracle/jyotishyamitra_steve_jobs_probe_2026_07_18.json`

The input contract issue was resolved: `input_birthdata()` returns string-valued input, while `generate_astrologicalData()` needs the numeric `get_birthdata()` object after `validate_birthdata() == "SUCCESS"`.

The Steve Jobs run now returns structured dictionary raw with top-level keys including `D1`, `D2`, `D4`, `D9`, `D10`, `Balas`, `AshtakaVarga`, and `Dashas`.

Replay stability:

- full raw hash: intentionally unstable because `$.Dashas.Vimshottari.current.date` embeds run time.
- normalized raw hash: stable after replacing `$.Dashas.Vimshottari.current.date` with `<volatile_run_time>`.
- normalized raw SHA-256: `b749d78f42a43aa4e5b647230a7e317602de21e3308a0a650c0e662c630546cf`
- schema SHA-256: `4ed38f03ddc8774b48501969c31c0a9ad87de3e2a4b5bc293cd86280467bc858`
- schema path count: `13524`

## Next

1. Extract D1/D2/D4/D9/D10, Shadbala/Balas, AshtakaVarga, and Vimshottari fields.
2. Compare field-by-field against local, Xalen, PyJHora, and jyotishganit as independent observation only.
3. Keep `promotion_allowed=false` unless external worked examples arbitrate method variants.
