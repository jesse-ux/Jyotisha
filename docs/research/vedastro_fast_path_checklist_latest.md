# VedAstro 596+ Nodes Fast-Path Checklist

- Generated: `2026-06-28T23:49:39.978828+00:00`
- Local registry techniques: `89`
- Official catalog tags: `46`
- Official catalog methods/events: `2258`

## Boundary

- Do not clone VedAstro wholesale into local code.
- Keep the local adjudicator as the final reasoning layer.
- Default all external outputs to secondary evidence unless explicitly promoted by local tests and contracts.

## Lane Breakdown

### Direct Official MCP

- `MCP / API Surface` [P0] - local=`partial`, adjudicator=`primary`; assets: mcp_server.py, jyotish_api_server.py, strict workflows, vedastro_service_adapter.py, vedastro_official_mcp_bridge.py
  route: If official MCP is available, that is the fastest direct agent path; otherwise fall back to local REST adapter.
  gap: Local API/MCP surfaces exist and the official public MCP bridge is live; REST adapter official endpoint smoke still depends on configured endpoint-backed execution.

### Official Python Bridge

- `Tajika Annual` [P0] - local=`partial`, adjudicator=`secondary`; assets: tajika.py, varshaphala.py, sahams, solar_return
  route: Use Python bridge for breadth, but keep year-chart reasoning and labels local.
  gap: Annual modules exist; yearly career/wealth/month windows need stronger strict-workflow integration.
- `Ashtakavarga` [P0] - local=`partial`, adjudicator=`secondary`; assets: ashtakavarga, ashtakavarga_pav, ashtakavarga_sodhita, finance_ashtakavarga_bridge
  route: Use the Python bridge for broad calculator access while local strict workflows stay authoritative.
  gap: SAV/BAV is in production; PAV/Sodhita/Kakshya bridges need continued regression before being dominant labels.
- `Shadbala` [P0] - local=`partial`, adjudicator=`secondary`; assets: shadbala, shadbala_advanced, shadbala_component_cap, oracle_shadbala_queue
  route: Broad strength calculators are easiest through the Python bridge, then folded back as oracle evidence.
  gap: Local component-aware cap exists; absolute external oracle closure is still incomplete.

### REST Adapter

- `EventsAtRange / Life Event Graph` [P0] - local=`partial`, adjudicator=`oracle_only`; assets: transit_trigger, dasha, narayana_dasha, vedastro_service_adapter.range_scan
  route: Use official REST adapter first for range scans; keep local adjudicator as the reasoning layer.
  gap: Local timing modules exist, but a high-frequency day/hour event graph is not yet a local productized radar.
- `Birth Time ML / Rectification Assistant` [P1] - local=`partial`, adjudicator=`secondary`; assets: birth_time_rectifier.py, rectification_gate, jyotish-app rectification
  route: Use VedAstro externally only as supporting evidence; local rectification gate stays in control.
  gap: Local rectification exists; ML parity with VedAstro-style service behavior is not established.

### Local Native Preferred

- `Prashna / Horary` [P0] - local=`covered`, adjudicator=`secondary`; assets: prashna.py, kp_system.py, upagraha_gulika_maandi, sphuta_trisphuta_family
  route: No need to outsource core horary math while local modules already exist.
  gap: Horary modules exist but are not yet a first-class question adjudicator route.
- `Jaimini / Chara Dasha` [P0] - local=`covered`, adjudicator=`secondary`; assets: jaimini.py, AK, DK, UL, Chara Dasha, Jaimini marriage bridge v1
  route: Keep Jaimini native; external engines help only as spot-check evidence.
  gap: Core Jaimini exists; mission/career/marriage quality adjudicator folding is not yet exhaustive.
- `Report Rendering` [P0] - local=`partial`, adjudicator=`not_used`; assets: report_artifact API, report_builder.py, chart_renderer.py, jyotish-app export
  route: Rendering is a local product concern, not a VedAstro dependency.
  gap: HTML/PDF artifact path exists; polished SVG/PDF chart rendering and cloud-scale report production are not finished.
- `Synastry / Ashtakoot` [P0] - local=`covered`, adjudicator=`secondary`; assets: synastry.py, ashtakoot.py, 36-point Ashtakoot, 16-factor compatibility
  route: Local matching is already stronger than a thin external call unless you need an oracle comparison.
  gap: Matching modules exist and API-backed; relationship adjudicator still needs a formal bridge.
- `D1-D60 Divisional Charts` [P0] - local=`covered`, adjudicator=`primary`; assets: varga, varga_full, shodasavarga, divisional_charts_extended
  route: Do not pay external-call cost here; local engine is already the primary route.
  gap: Local varga coverage is strong; keep VedAstro/PyJHora as benchmark evidence rather than replacing local math.

### Hybrid Router

- `Ayanamsa Selection` [P0] - local=`partial`, adjudicator=`oracle_only`; assets: ayanamsa_utils, ephemeris_adapter_contract
  route: Prefer local ayanamsa controls for production and use VedAstro only as parity/oracle evidence.
  gap: Local Lahiri path is usable, but broad ayanamsa parity and public comparison artifacts remain incomplete.

### External Evidence Only

- `Numerology / Non-Jyotish Tools` [P2] - local=`missing`, adjudicator=`not_used`; assets: -
  route: Do not implement locally unless it becomes product-critical.
  gap: Adjacent product feature; not required for Jyotish adjudicator depth.

## Immediate Execution Order

1. Use `Direct Official MCP` where an official MCP surface is available to agents.
2. Use `Official Python Bridge` for broad calculator access that does not need browser/session orchestration.
3. Use `REST Adapter` for range scans and endpoint-style external evidence.
4. Keep `Local Native Preferred` rows local; do not waste time rebuilding what is already stronger here.
5. Use `Hybrid Router` only where parity or oracle closure still matters more than raw breadth.

