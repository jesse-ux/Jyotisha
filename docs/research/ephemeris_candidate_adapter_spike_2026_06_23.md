# Ephemeris Candidate Adapter Spike - 2026-06-23

Purpose: decide whether a non-default `candidate_backend` is ready to enter the `EphemerisAdapterContract` parity gate.

Run:

```bash
python3 scripts/ephemeris_candidate_adapter_spike.py
```

## swisseph_wasm_candidate

`swisseph_wasm_candidate` has local browser assets and package dependencies, so it is a plausible offline/PWA candidate. It is not a separate accuracy authority and it is not ready for `runtime_setting_exposure`.

The `license_gate` is the important blocker: Swiss Ephemeris WASM still follows Swiss Ephemeris licensing boundaries, so distribution claims must be reviewed before this becomes a user-selectable backend.

The local package metadata currently reports:

| Package | `package_license` |
|---|---|
| `@swisseph/browser` | `AGPL-3.0` |
| `swisseph-wasm` | `GPL-3.0-or-later` |

That means the WASM path is useful for local/PWA fallback experiments, but it must not be treated as a low-risk proprietary desktop dependency without a license decision.

## xalen_ephemeris_candidate

`xalen_ephemeris_candidate` remains the best permissive-direction spike because `vedika-io/xalen-ephemeris` is tracked as Apache-2.0. There is no local executable mirror in this workspace yet, so the current spike status is documentation-only.

## Gate

Both candidates are blocked until `parity_gate_required` is satisfied:

1. Produce rows matching `EphemerisAdapterContract`.
2. Compare against `swisseph_python` baseline rows.
3. Pass `longitude_delta_arcsec` thresholds for Sun, Moon, Ascendant, Rahu, and Ketu.
4. Preserve `ayanamsa_value`, `retrograde`, backend metadata, node policy, and house policy.
5. Keep `runtime_setting_exposure` blocked until the above is verified.

Decision: do not expose any non-SwissEph runtime setting yet. The next implementation step is an isolated executable adapter only after local assets and license review are complete.
