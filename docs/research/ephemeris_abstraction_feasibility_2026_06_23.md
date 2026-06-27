# Ephemeris Abstraction Feasibility - 2026-06-23

Purpose: make the ephemeris roadmap probeable instead of relying on UI labels or memory from prior windows.

## candidate_backends

| Backend | Current role | replacement_readiness | license_posture | Decision |
|---|---|---|---|---|
| `swisseph_python` | Primary local Python API path through `scripts/jyotish_api_server.py` | `primary` | Current Swiss Ephemeris boundary must stay explicit in settings, exports, and docs | Keep as canonical longitude source |
| `swisseph_wasm` | Browser/local-first degradation path through bundled WASM assets and `@swisseph/browser` / `swisseph-wasm` dependencies | `fallback` | Same Swiss Ephemeris boundary as the Python path | Keep as fallback, not a separate accuracy oracle |
| `xalen_ephemeris` | External Apache-2.0 Rust candidate from `vedika-io/xalen-ephemeris` | `spike_only` | Favorable for experiments, but no local adapter or parity matrix exists yet | Do not expose as real runtime replacement until a parity spike passes |
| `vedastro` | MIT full-stack product/API benchmark and service-boundary adapter candidate | `service_adapter_candidate` | Can inform API, OpenAPI, chat, Panchanga, and product workflow design; C# core should stay behind an API/service boundary if reused | Reuse product/API ideas and progress through an adapter contract, not as a drop-in Python ephemeris |
| `pyjhora_benchmark` | Broad JHora-style behavior/oracle benchmark | `benchmark_only` | AGPL; do not copy implementation code into this app unless the whole downstream license posture is changed | Use only expected outputs, public examples, and behavior comparisons |

## Probe

Run:

```bash
python3 scripts/ephemeris_backend_probe.py
```

The probe returns JSON with `candidate_backends`, `license_posture`, and `replacement_readiness`. It is intentionally read-only and network-free, so it can be used in regression checks without mutating user data or depending on GitHub availability.

## Engineering Decision

The app already records `ephemerisBackend` in calculation settings and export provenance. That is useful, but it is not enough to claim backend replacement. The real next step is an adapter contract:

- input: UTC datetime, latitude, longitude, ayanamsa policy, node policy, body list
- output: tropical longitude, sidereal longitude, speed, retrograde flag, ayanamsa value, backend metadata
- parity gate: compare Moon, Sun, Ascendant, Rahu/Ketu, and daily boundary cases against `swisseph_python`
- acceptance: document max deltas before any new backend can be selectable as a runtime calculation source

Until that exists, `swisseph_python` remains the production source, `swisseph_wasm` remains the fallback, `xalen_ephemeris` remains a spike candidate, `vedastro` remains a gated service-adapter candidate, and `pyjhora_benchmark` remains an AGPL behavior benchmark only.
