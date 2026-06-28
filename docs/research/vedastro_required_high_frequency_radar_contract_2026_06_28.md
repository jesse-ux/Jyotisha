# VedAstro Required High-Frequency Radar Contract - 2026-06-28

## Scope

This pass turns VedAstro from an optional comparison note into a required
external timing-radar boundary for strict event workflows.

The local engine still owns final adjudication. VedAstro is used as an external
high-frequency calculation/event source, especially for range timing.

## Official Surface Interpreted

Public VedAstro surfaces reviewed on 2026-06-28:

- `https://vedastro.org/APIBuilder.html`
  - General API Builder surface.
  - Treated as the broad calculator layer, advertised by VedAstro as 600+
    calculators.
- `https://vedastro.org/EventsChartAPIBuilder.html`
  - Events API Builder surface.
  - Page metadata describes three event timing endpoints:
    `SearchEvents`, `GetEventTiming`, `ListEventTypes`.
  - Page metadata describes 400+ pre-defined events.
  - The UI exposes `Scan precision (hours)`, confirming that the events surface
    is a range-scan / high-frequency timing tool, not a fixed life-category
    dictionary.
- `https://pypi.org/pypi/vedastro/json`
  - Current observed Python package version: `1.23.25`.
  - The local contract keeps the project-level claim as `596+` calculations
    because that is the Python-library surface previously documented in this
    project.

## Adapter Contract

`scripts/vedastro_service_adapter.py --print-schema` now exposes:

```json
{
  "vedastro_calculation_coverage": {
    "official_python_library_calculations": "596+",
    "official_api_builder_calculators": "600+",
    "official_events_builder_events": "400+",
    "official_events_builder_methods": [
      "SearchEvents",
      "GetEventTiming",
      "ListEventTypes"
    ],
    "range_scan_role": "high_frequency_life_event_radar",
    "intended_use": "external_timing_evidence_for_strict_workflow"
  }
}
```

Range-scan request previews now include:

```json
{
  "operation": "range_scan",
  "vedastro_event_method": "SearchEvents"
}
```

The adapter remains configurable through `VEDASTRO_API_ENDPOINT` and gated by
`VEDASTRO_ENABLE_NETWORK`. If the endpoint or network flag is absent, it returns
a controlled preview / blocked status instead of fabricating external evidence.

## Strict Workflow Contract

For `career`, `relationship`, and `finance` strict workflows:

- `present_evidence.external_activation` is required as the VedAstro timing
  radar slot.
- If no VedAstro range-scan ledger is supplied, the slot becomes:

```json
{
  "level": "missing_required_external_radar",
  "source": "vedastro_service_adapter_candidate",
  "required": true,
  "operation": "range_scan"
}
```

- `event_judgement.secondary_context` receives
  `vedastro_range_scan_missing`.
- `technique_audit` receives a blocked row:

```json
{
  "technique": "VedAstro EventsAtRange / 596+ Calculator Radar",
  "status": "blocked",
  "role": "required_external_timing_radar",
  "effect": "confidence_boundary_only_no_score_or_label_lift"
}
```

When valid VedAstro range-scan events are supplied, the audit row changes to
`status = used`, with `event_count`.

## Boundary

VedAstro range-scan evidence may support timing context, but it must not bypass
the local core gates:

- It does not replace Vimshottari + Narayana dual dasha.
- It does not replace D9/UL, D2/D10, Shadbala, Ashtakavarga, Jaimini, or
  Functional Benefic/Malefic layers.
- It does not directly set `dominant_label` or `payout_label`.
- It cannot bypass missing local promise layers; tests verify that a missing
  `wealth_promise_strength` still caps the finance score even when VedAstro
  range evidence is present.

## Verification

Fresh verification:

- `python3 -m pytest tests/test_vedastro_service_adapter_executor.py tests/test_vedastro_external_technique_evidence.py tests/test_vedastro_parity_matrix.py tests/test_vedastro_adapter_candidate_guard.py -q`
- `python3 -m pytest tests/test_mcp_strict_workflow_finance.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_career.py tests/test_life_event_graph_v1.py -q`

