# Monthly Adjudication Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the old month-facing "opportunity / pressure" simplification with a route-aware monthly adjudication structure for career, relationship, and finance that reuses existing strict workflow evidence.

**Architecture:** Reuse `mcp_server.py` strict workflow evidence as the single source, derive a lightweight `monthly_adjudication_summary` from existing promise/activation/manifestation layers plus VedAstro official day signals, then surface it through prompt-pack, guided topics, AI chat context, and frontend cards. Keep `official_day_signal_summary` as a compatibility layer during the transition.

**Tech Stack:** Python, existing strict workflow builders, pytest, current guided-topic/frontend consumers.

## Global Constraints

- Reuse current strict workflow collectors before adding new collectors.
- Reuse current `event_judgement`, `adjudication_stages`, and `official_day_signal_summary` outputs.
- Do not add new heavy VedAstro calls for this task.
- Keep `Functional Benefic/Malefic`, relevant vargas, and `Vimshottari + Narayana` hard gates visible.
- Preserve `blocked`, `conflicts`, and `confidence_cap` honesty boundaries.

---

### Task 1: Define and test the new contract

- [ ] Add failing backend tests for `monthly_adjudication_summary` in career/relationship/finance strict workflow tests.
- [ ] Add failing guided-topic and frontend tests asserting the new field is carried and displayed.

### Task 2: Implement route-aware monthly adjudication

- [ ] Add helper builders in `<repo>/mcp_server.py`.
- [ ] Attach `monthly_adjudication_summary` to strict workflow contracts.
- [ ] Keep `official_day_signal_summary` unchanged for compatibility.

### Task 3: Surface the contract through consumers

- [ ] Add `monthly_adjudication_summary` to compact prompt-pack contracts in `<repo>/scripts/jyotish_engine.py`.
- [ ] Add it to guided topics in `<repo>/scripts/guided_topic_discovery.py`.
- [ ] Expose it in `<repo>/jyotish-app/main.js` and `<repo>/jyotish-app/ai-chat.js`.

### Task 4: Verify targeted regressions

- [ ] Run the strict workflow tests for career/relationship/finance.
- [ ] Run the guided-topic smoke test.
- [ ] Run the targeted frontend productization assertions.
