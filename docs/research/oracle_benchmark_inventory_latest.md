# Oracle Benchmark Single-Truth Inventory

Generated: `2026-06-28T07:20:42.378403+00:00`

## Summary

- oracle_registry_count: `3`
- oracle_case_count: `9`
- evidence_template_count: `4`
- pending_packet_count: `19`
- pending_pyjhora_packet_count: `8`
- pending_non_pyjhora_packet_count: `11`
- pyjhora_artifact_count: `8`
- dashboard_count: `4`

## Oracle Registries

- `references/oracle/ashtakoot_oracle_cases.json` (ashtakoot)
- `references/oracle/dasha_shadbala_oracle_cases.json` (shadbala)
- `references/oracle/tajika_annual_oracle_cases.json` (tajika_sahams)

## Oracle Case Files

- `references/oracle/cases/albert_einstein.json` (general)
- `references/oracle/cases/elon_musk.json` (general)
- `references/oracle/cases/equator_quito.json` (general)
- `references/oracle/cases/historical_dst_london_1943.json` (general)
- `references/oracle/cases/katy_perry.json` (general)
- `references/oracle/cases/marilyn_monroe.json` (general)
- `references/oracle/cases/polar_reykjavik.json` (general)
- `references/oracle/cases/steve_jobs.json` (general)
- `references/oracle/cases/private_case_redacted.json` (general)

## Pending Evidence Packets

- `references/oracle/artifacts/pending_packets/capture_manifest.json` (general, status: `unknown`, case: `capture_manifest.json`)
- `references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json` (tajika_sahams, status: `draft`, case: `template_einstein_varshaphala_1905_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_extreme_latitude_kp.json` (general, status: `draft`, case: `template_extreme_latitude_kp`)
- `references/oracle/artifacts/pending_packets/external_template_extreme_latitude_kp_pyjhora_20260627.json` (general, status: `external_verified`, case: `template_extreme_latitude_kp`)
- `references/oracle/artifacts/pending_packets/external_template_synthetic_north_china_shadbala_raman.json` (shadbala, status: `draft`, case: `template_synthetic_north_china_shadbala_raman`)
- `references/oracle/artifacts/pending_packets/external_template_synthetic_north_china_shadbala_raman_pyjhora_20260627.json` (shadbala, status: `external_verified`, case: `template_synthetic_north_china_shadbala_raman`)
- `references/oracle/artifacts/pending_packets/external_template_historical_dst_london_varshaphala_1943_lahiri.json` (tajika_sahams, status: `draft`, case: `template_historical_dst_london_varshaphala_1943_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_historical_epoch_lahiri.json` (dasha, status: `draft`, case: `template_historical_epoch_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_historical_epoch_lahiri_pyjhora_20260627.json` (dasha, status: `external_verified`, case: `template_historical_epoch_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_marilyn_monroe_varshaphala_1962_lahiri.json` (tajika_sahams, status: `draft`, case: `template_marilyn_monroe_varshaphala_1962_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_steve_jobs_dasha_lahiri.json` (dasha, status: `draft`, case: `template_steve_jobs_dasha_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_steve_jobs_dasha_lahiri_pyjhora_20260627.json` (dasha, status: `external_verified`, case: `template_steve_jobs_dasha_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_steve_jobs_shadbala_lahiri_pyjhora_20260627.json` (shadbala, status: `external_verified`, case: `template_steve_jobs_dasha_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_steve_jobs_varshaphala_1984_lahiri.json` (tajika_sahams, status: `external_verified`, case: `template_steve_jobs_varshaphala_1984_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_steve_jobs_varshaphala_1984_lahiri_pyjhora_20260627.json` (tajika_sahams, status: `external_verified`, case: `template_steve_jobs_varshaphala_1984_lahiri`)
- `references/oracle/artifacts/pending_packets/external_template_synthetic_extreme_latitude_varshaphala_kp.json` (tajika_sahams, status: `draft`, case: `template_synthetic_extreme_latitude_varshaphala_kp`)
- `references/oracle/artifacts/pending_packets/external_template_private_oracle_redacted.json` (shadbala, status: `draft`, case: `template_private_oracle_redacted`)
- `references/oracle/artifacts/pending_packets/external_template_private_oracle_redacted_pyjhora_20260627.json` (shadbala, status: `external_verified`, case: `template_private_oracle_redacted`)
- `references/oracle/artifacts/pending_packets/external_template_private_oracle_shadbala_redacted.json` (shadbala, status: `external_verified`, case: `template_private_oracle_redacted`)

## PyJHora Black-Box Assets

- `references/oracle/artifacts/pyjhora_extreme_latitude_kp_shadbala_stdout_20260627.txt` (shadbala)
- `references/oracle/artifacts/pyjhora_synthetic_north_china_shadbala_raman_stdout_20260627.txt` (shadbala)
- `references/oracle/artifacts/pyjhora_historical_epoch_dasha_stdout_20260627.txt` (dasha)
- `references/oracle/artifacts/pyjhora_steve_jobs_dasha_stdout_20260627.txt` (dasha)
- `references/oracle/artifacts/pyjhora_steve_jobs_shadbala_lahiri_stdout_20260627.txt` (shadbala)
- `references/oracle/artifacts/pyjhora_steve_jobs_varshaphala_1984_lahiri_stdout_20260627.txt` (tajika_sahams)
- `references/oracle/artifacts/private_oracle_redacted_dasha_stdout.txt` (dasha)
- `references/oracle/artifacts/private_oracle_redacted_shadbala_stdout.txt` (shadbala)

Manifest: `references/oracle/artifacts/pyjhora_oracle_artifact_manifest.json`

## Dashboards

- `docs/research/oracle_closure_master_dashboard_latest.md`
- `docs/research/public_benchmark_dashboard_latest.md`
- `docs/research/tajika_annual_benchmark_dashboard_latest.md`
- `docs/research/tajika_annual_closure_status_latest.md`

## Boundary

This inventory tracks external oracle evidence only. It does not import PyJHora/JHora implementation code, does not tune production constants, and does not treat internal consistency as external validation.

## Next Actions

- Promote verified pending packets into the relevant oracle registry only after metadata and source_artifact pass validation.
- Keep PyJHora outputs as black-box artifacts and regenerate the artifact manifest after each external capture batch.
- Update public_benchmark_dashboard_latest.md after each validated packet batch so public claims stay conservative.
- Use this inventory before changing strict workflow or adjudicator logic that depends on external truth.
