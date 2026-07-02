# VedAstro Gateway + Web Professional Reading v1 Status

Date: 2026-07-02

## Implemented

- Added `scripts/vedastro_gateway.py` with backend selection for `self_host`, `official`, `cache`, `queue`, and `local_fallback`.
- Added gateway status and run packet contracts.
- Exposed API endpoints:
  - `/api/vedastro_gateway/status`
  - `/api/vedastro_gateway/run`
  - `/api/professional_reading`
- Added Web Professional Reading v1 frontend panel in Trust Center.
- Added frontend API bridge functions:
  - `getVedAstroGatewayStatus`
  - `runVedAstroGateway`
  - `runProfessionalReading`
- Added AI Chat context support for `Professional Reading Packet`.
- Added `.env.cn.example` and README documentation for Mainland China gateway mode.

## Verification

Passed:

- `python3 -m pytest tests/test_vedastro_gateway.py -q`
- `python3 -m pytest tests/test_api_server_security.py -k "vedastro_gateway or professional_reading or vedastro_range_scan" -q`
- `python3 -m pytest tests/test_frontend_productization.py -k "professional_reading or ai_chat_consumes_professional or cn_gateway" -q`
- `python3 -m pytest tests/test_vedastro_gateway.py tests/test_vedastro_user_entrypoint.py tests/test_vedastro_official_capability_runner.py tests/test_api_server_security.py -k "vedastro_gateway or professional_reading or vedastro_user_entrypoint or official_capability" -q`
- `python3 -m pytest tests/test_frontend_productization.py -k "professional_reading or cn_gateway or ai_chat_consumes_professional" -q`
- `npm run build --prefix jyotish-app`
- `JYOTISH_SKIP_LOCAL_ENV=1 VEDASTRO_FULL_CATALOG_SAMPLE_LIMIT=0 python3 scripts/vedastro_user_entrypoint.py ... --format markdown`
- `JYOTISH_SKIP_LOCAL_ENV=1 VEDASTRO_GATEWAY_MODE=cn_gateway VEDASTRO_CACHE_TTL_SECONDS=604800 VEDASTRO_FULL_CATALOG_SAMPLE_LIMIT=0 python3 - <<'PY' ...`

Quick quality gate:

- `python3 scripts/run_quality_gate.py --profile quick --skip-frontend-runtime` passed compile, JSON validation, capability audit, fragment audit, character inventory manifest, deployment preflight, and BPHS invariant checks.
- It was manually interrupted after more than 10 minutes with no new output while running the broad pytest bundle:
  `tests/test_frontend_productization.py tests/test_cli_smoke.py tests/test_api_server_security.py tests/test_jaimini.py tests/test_shadbala_complete.py tests/test_transit_trigger.py tests/test_oracle_collection_queue.py tests/test_oracle_evidence_validator.py tests/test_external_oracle_sanity_closure.py`.
- This interruption is recorded as incomplete verification, not a pass.

## Boundary

- Mainland China users do not need browser access to `vedastro.org` or `api.vedastro.org`.
- Browser code does not expose VedAstro secrets.
- Gateway packets do not claim all 641 official methods were executed.
- Local Jyotish computation remains available when VedAstro upstream is blocked, queued, cached, or unavailable.
