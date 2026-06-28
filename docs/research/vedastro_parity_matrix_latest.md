# VedAstro Parity Matrix

- Generated: `2026-06-28T23:49:39.845848+00:00`
- Rows: `13`
- P0 rows: `11`
- Local registry technique count: `89`

## Honesty Boundary

VedAstro calls are external adapter evidence until a capability is promoted by local tests, oracle artifacts, or strict workflow integration. This matrix does not claim clone-level parity.

## Summary

- Local status counts: `{"covered": 4, "missing": 1, "partial": 8}`
- Recommended path counts: `{"external_evidence_only": 1, "hybrid_local_plus_vedastro": 7, "local_native": 4, "new_local_impl": 1}`
- Fastest path lane counts: `{"external_evidence_only": 1, "hybrid_router": 1, "local_native_preferred": 5, "official_mcp": 1, "official_python_bridge": 3, "rest_adapter": 2}`

## Matrix

| VedAstro capability | Category | Local status | Path | Fastest lane | Priority | Adjudicator use | Local assets | Gap notes |
|---|---|---:|---|---|---:|---|---|---|
| Tajika Annual | annual_prediction | partial | hybrid_local_plus_vedastro | official_python_bridge | P0 | secondary | tajika.py, varshaphala.py, sahams, solar_return | Annual modules exist; yearly career/wealth/month windows need stronger strict-workflow integration. |
| Ayanamsa Selection | ephemeris_policy | partial | hybrid_local_plus_vedastro | hybrid_router | P0 | oracle_only | ayanamsa_utils, ephemeris_adapter_contract | Local Lahiri path is usable, but broad ayanamsa parity and public comparison artifacts remain incomplete. |
| Prashna / Horary | horary | covered | local_native | local_native_preferred | P0 | secondary | prashna.py, kp_system.py, upagraha_gulika_maandi, sphuta_trisphuta_family | Horary modules exist but are not yet a first-class question adjudicator route. |
| Jaimini / Chara Dasha | jaimini | covered | local_native | local_native_preferred | P0 | secondary | jaimini.py, AK, DK, UL, Chara Dasha, Jaimini marriage bridge v1 | Core Jaimini exists; mission/career/marriage quality adjudicator folding is not yet exhaustive. |
| Report Rendering | presentation | partial | new_local_impl | local_native_preferred | P0 | not_used | report_artifact API, report_builder.py, chart_renderer.py, jyotish-app export | HTML/PDF artifact path exists; polished SVG/PDF chart rendering and cloud-scale report production are not finished. |
| Synastry / Ashtakoot | relationship_matching | covered | local_native | local_native_preferred | P0 | secondary | synastry.py, ashtakoot.py, 36-point Ashtakoot, 16-factor compatibility | Matching modules exist and API-backed; relationship adjudicator still needs a formal bridge. |
| MCP / API Surface | service_surface | partial | hybrid_local_plus_vedastro | official_mcp | P0 | primary | mcp_server.py, jyotish_api_server.py, strict workflows, vedastro_service_adapter.py, vedastro_official_mcp_bridge.py | Local API/MCP surfaces exist and the official public MCP bridge is live; REST adapter official endpoint smoke still depends on configured endpoint-backed execution. |
| Ashtakavarga | strength | partial | hybrid_local_plus_vedastro | official_python_bridge | P0 | secondary | ashtakavarga, ashtakavarga_pav, ashtakavarga_sodhita, finance_ashtakavarga_bridge | SAV/BAV is in production; PAV/Sodhita/Kakshya bridges need continued regression before being dominant labels. |
| Shadbala | strength | partial | hybrid_local_plus_vedastro | official_python_bridge | P0 | secondary | shadbala, shadbala_advanced, shadbala_component_cap, oracle_shadbala_queue | Local component-aware cap exists; absolute external oracle closure is still incomplete. |
| EventsAtRange / Life Event Graph | timing_range_scan | partial | hybrid_local_plus_vedastro | rest_adapter | P0 | oracle_only | transit_trigger, dasha, narayana_dasha, vedastro_service_adapter.range_scan | Local timing modules exist, but a high-frequency day/hour event graph is not yet a local productized radar. |
| D1-D60 Divisional Charts | varga | covered | local_native | local_native_preferred | P0 | primary | varga, varga_full, shodasavarga, divisional_charts_extended | Local varga coverage is strong; keep VedAstro/PyJHora as benchmark evidence rather than replacing local math. |
| Birth Time ML / Rectification Assistant | birth_time_rectification | partial | hybrid_local_plus_vedastro | rest_adapter | P1 | secondary | birth_time_rectifier.py, rectification_gate, jyotish-app rectification | Local rectification exists; ML parity with VedAstro-style service behavior is not established. |
| Numerology / Non-Jyotish Tools | adjacent_tools | missing | external_evidence_only | external_evidence_only | P2 | not_used | - | Adjacent product feature; not required for Jyotish adjudicator depth. |

## Next Actions

1. Promote `VedAstro adapter MVP` from contract to endpoint-backed smoke tests.
2. Add a relationship bridge for `Synastry / Ashtakoot` before using matching scores as primary labels.
3. Build `Life Event Graph v1` from local monthly/day scan plus optional VedAstro range-scan evidence.
4. Keep ayanamsa and Shadbala parity under oracle closure before claiming production tuning.

