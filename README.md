# Jyotish Vedic Astrology — AI-Native Full-Reading System

> **What makes this different:** This is not a calculator. It is an AI-native Jyotish analysis system that combines calculation engines, interpretive workflows, confidence auditing, and graceful degradation — organized into a reproducible full-reading pipeline.

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Techniques](https://img.shields.io/badge/techniques-44-blueviolet)](references/technique_registry.json)
[![Covered](https://img.shields.io/badge/covered-26-green)](references/technique_registry.json)
[![Partial](https://img.shields.io/badge/partial-18-orange)](references/technique_registry.json)

---

## Table of Contents

- [What Is This](#what-is-this)
- [Quick Start](#quick-start)
- [Core Workflow](#core-workflow)
- [Technique Coverage](#technique-coverage)
- [Why This Exists (Competitive Context)](#why-this-exists)
- [Honest Assessment](#honest-assessment)
- [Project Status](#project-status)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## What Is This

This is a **Vedic (Jyotish) astrology analysis system** designed for deep, auditable full-chart readings. It is NOT a simple ephemeris calculator — it is a multi-stage interpretive pipeline that:

1. **Computes** divisional charts (D1/D9/D10/...) via Swiss Ephemeris
2. **Runs** 44+ techniques (Dashas, Yogas, Shadbala, Ashtakavarga, Transits...)
3. **Routes** the analysis through strict workflow paths depending on question type (career / relationship / wealth / timing)
4. **Audits** every technique used — declaring what was called, what was partial, what was missing, and how that affects confidence
5. **Degrades gracefully** — partial techniques are labeled, not silently over-promising

### Key Differentiators (vs. PyJHora / VedAstro / Maitreya)

| Feature | This Project | PyJHora | VedAstro | Maitreya |
|---------|-------------|----------|----------|----------|
| Full-reading pipeline (one command) | ✅ | ❌ | ❌ | ❌ |
| Strict workflow router (per-question-type) | ✅ | ❌ | ❌ | ❌ |
| Technique Audit Table (confidence labeling) | ✅ | ❌ | ❌ | ❌ |
| Capability degradation (partial ≠ covered) | ✅ | ❌ | ❌ | ❌ |
| MEVG external verification gates | ✅ | ❌ | ❌ | ❌ |
| 44+ techniques integrated | ✅ | ✅ (50+) | ✅ (200+) | ✅ |
| Traditional algorithm benchmarked | 🔶 partial | ✅ | ✅ | ✅ |
| Docker / MCP Server | 🔶 planned | ❌ | ✅ | ❌ |
| English docs / PyPI package | 🔶 in progress | ✅ | ✅ | ✅ |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Swiss Ephemeris (`pyswisseph` or `ephem`)
- Optional: `pypdf`, `pdfplumber` (for PDF chart input)

### Install

```bash
# Clone the repository
git clone https://github.com/732642856/yinduzhanxing.git
cd yinduzhanxing

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python3 scripts/audit_capabilities.py --mode validate
# Expected: valid=true, problem_count=0
```

### Minimal Full Reading (5 minutes)

```bash
python3 scripts/jyotish_engine.py full-reading \
  --year 1990 --month 6 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6139 --lon 77.2090 --tz 5.5 \
  --age 36 \
  --transit-date 2026-06-04
```

**Output:** ~45 computed modules, zero errors, complete structured reading with technique audit table.

### Sample Output (abbreviated)

```
═══ FULL READING ═══
Birth Data: 1990-06-15 10:30  (+5.5) 28.61°N 77.21°E
Lagna: Gemini   Sun: Taurus   Moon: Leo

── Static Analysis ──
[✓] D1 Rashi Chart
[✓] D9 Navamsa
[✓] D10 Dasamsa
[✓] Vimshottari Dasha (120 years)
[✓] Ashtakavarga (8-point system)
[✓] Shadbala (partial — internal invariants pass, external calibration pending)
[✓] Yogas & Doshas
[✓] Argala (planetary interventions)
[✓] Nakshatra Advanced (Chandra Bala / Tara Bala)

── Dynamic Timing ──
[✓] Vimshottari Dasha breakdown
[✓] Dasha Sandhi detection
[✓] Transit (true positions)
[✓] Double Transit analysis
[✓] Narayana Dasha
[✓] Solar Return / Varshaphala (partial)
[✓] Nakshatra Dasha (Ashtottari)

── Technique Audit Table ──
✓ Vimshottari Dasha        covered      high confidence
✓ Ashtakavarga             covered      high confidence
🔶 Shadbala                partial      internal consistent, external calibration pending
🔶 Chara Dasha             partial      simplified (24% match with PyJHora KN Rao)
❌ KP Sub-Lord              missing      not yet implemented
```

---

## Core Workflow

### Three Input Paths

| Path | Input | Behavior |
|------|-------|----------|
| **A: Precise birth data** | Date + time + coordinates | Full `full-reading` engine |
| **B: PDF / text chart** | Scanned chart or description | Extract → Quality Gate → route to A |
| **C: Uncertain birth time** | "Don't know my birth time" | Interactive birth time rectification |

### Eight-Stage Pipeline

```
Stage -1: Question-type routing (career / relationship / wealth / timing)
Stage 0:  Input routing (A / B / C)
Stage 1:  (B only) PDF extraction + Quality Gate
Stage 2:  Intent recognition → target house routing
Stage 3:  Static analysis (10 steps)
Stage 4:  Dynamic timing (7 steps)
Stage 5:  Timing output (5-layer verification)
Stage 6:  Remedial measures (optional)
Stage 7:  Modern language packaging
Stage 8:  Technique Audit Table (mandatory)
```

**Strict Workflow Router** (`references/strict-workflow-router.md`):
- Career questions → `career-timing-strict`
- Relationship questions → `relationship-timing-strict`
- Wealth questions → `wealth-timing-strict`
- Event timing → `event-timing-strict`
- Historical verification → `event-verification-strict`

The AI does NOT require the user to name techniques (e.g., "Chara Dasha"). It auto-selects based on question type.

---

## Technique Coverage

Current count: **44 techniques** (26 covered, 18 partial, 0 missing)

| Technique | Status | Notes |
|-----------|--------|-------|
| D1 Rashi Chart | ✅ covered | Swiss Eph base |
| D9 Navamsa | ✅ covered | |
| D10 Dasamsa | ✅ covered | |
| Vimshottari Dasha | ✅ covered | |
| Dasha Sandhi | ✅ covered | |
| Ashtakavarga | ✅ covered | BPHS/PVR calibrated |
| Argala | ✅ covered | |
| Vargottama | ✅ covered | |
| Pushkara | ✅ covered | |
| A10 / Karma Pada | ✅ covered | |
| UL / Upapada | ✅ covered | |
| Transit (true positions) | ✅ covered | |
| Double Transit | ✅ covered | |
| Nakshatra Advanced | 🔶 partial | Engineering usable, needs more external benchmarking |
| Narayana Dasha | 🔶 partial | Usable, needs traditional benchmark |
| Solar Return / Varshaphala | 🔶 partial | Usable, some degradation logic present |
| **Shadbala** | 🔶 partial | **1200/1200 internal invariants pass; external absolute calibration NOT yet done** |
| **Chara Dasha** | 🔶 partial | **~24% match with PyJHora KN Rao method; do NOT use for high-confidence timing** |
| KP Sub-Lord | 🔶 partial | Simplified 9-equal division; not full KP |
| Bhava Chalit | 🔶 partial | Whole-sign adapter present; not full cusp-based reassignment |
| Sudarshana Chakra | 🔶 partial | D1×D9×D10 triangle verification; not traditional full implementation |
| Tajika Yogas | 🔶 partial | Simplified rules |
| Raj Yoga | 🔶 partial | Classic combinations covered; not all variants |
| Dhana Yoga | 🔶 partial | |
| Pancha Mahapurusha | 🔶 partial | |
| Neecha Bhanga | 🔶 partial | |
| Sade Sati | 🔶 partial | Simplified model |
| Tithi Lord | 🔶 partial | |
| Pancha Pakshi | 🔶 partial | |
| Rashi Tulya Navamsa | 🔶 partial | |
| Trimshamsa D30 | 🔶 partial | |
| Marriage Counting | 🔶 partial | Bhrigu Pada approximation |
| Prashna Integration | 🔶 partial | Not fully integrated into full-reading |
| Bhrigu Pada Dasha | 🔶 partial | Generic approximation |
| Muhurta | 🔶 partial | Panchanga elements present |

**Legend:**
- ✅ `covered` — implemented and benchmarked against authoritative sources
- 🔶 `partial` — implemented but NOT fully benchmarked; suitable for auxiliary reference only
- ❌ `missing` — not yet implemented

---

## Why This Exists (Competitive Context)

### The Landscape

| Project | Type | Strength | Weakness |
|---------|------|----------|-----------|
| **PyJHora** | Calculation library | Strongest traditional algorithm coverage (50+ Dashas, 284 Yogas) | No interpretive pipeline; user must interpret results themselves |
| **VedAstro** | API / Web platform | 200+ endpoints, Docker, MCP Server, MIT license | Interpretive audit & confidence labeling weaker |
| **Maitreya** | Desktop software | Mature cross-platform GUI | Jyotish depth not as deep as specialized projects |
| **jyotisha** | Panchanga / calendar | Excellent Panchanga accuracy | Not a full reading system |
| **This project** | AI-native analysis system | Full pipeline + audit + degradation | Pure calculation accuracy still being benchmarked |

### Our Position

> **PyJHora is the calculator. VedAstro is the API platform. Maitreya is the desktop software. This project is the "AI-native Jyotish research analyst."**

We are NOT trying to out-calculate PyJHora (it has years of lead). Our value is in:
1. Organizing calculations into a **reproducible interpretive workflow**
2. **Auditing** every technique used and declaring confidence
3. **Degrading gracefully** — partial techniques are labeled, not silently over-promising
4. Being **AI-native** — designed for integration with LLM-based analysis

---

## Honest Assessment

We believe in transparency about limitations. This is NOT a "99% accurate" system, and anyone claiming that about Jyotish is over-selling.

### Current Accuracy Estimates (self-evaluated)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Astronomical foundation (Swiss Eph) | 8.5/10 | Depends on ayanamsa, node mode, house system |
| Traditional algorithm accuracy | 7.3/10 | Chara Dasha & Shadbala need external calibration |
| Technique coverage breadth | 8.6/10 | 44 techniques, broad but not deepest |
| Reading detail depth | 9.6/10 | Possibly best among open-source projects |
| Prediction workflow rigor | 8.8/10 | Strict routing + audit table |
| Verification system | 8.2/10 | Has registry, benchmark, degradation; some verification still internal |
| Engineering maturity | 6.8/10 | Functional, but not productized (no Docker / PyPI / CI yet) |
| Open-source influence | 5.5/10 | Currently more of a "private high-density toolkit" |

### What "Partial" Means (Important)

When a technique is labeled `partial`:
- It CAN produce output
- The output has NOT been benchmarked against PyJHora / JHora / canonical texts
- It should be used as **auxiliary reference only**
- It must NOT be the sole basis for high-confidence predictions

Examples:
- `Shadbala` (partial): Internal invariants pass (1200/1200). External absolute values NOT calibrated. Use for relative strength ranking only.
- `Chara Dasha` (partial): ~24% match with PyJHora KN Rao method. Do NOT use for precise timing.

---

## Project Status

**Current version:** `v6.1.10-dk-rtn-theme-bridge`

### Recently Completed

- `v6.1.10` — Darakaraka deep reader wired into `full-reading.modules.jaimini.darakaraka`; thematic reports now consume real DK and Rashi Tulya Navamsa evidence.
- `v6.1.9` — Public/sanitized benchmark suite, competitive research, coverage roadmap and PDF validation methodology added.
- `v6.1.8` — Yoga validation reached F1=95.22% (FP=36, FN=63); thematic reports consume real `full-reading.modules` evidence.
- `v6.1.6` — Five-system Dasha convergence wired into full-reading (Vimshottari + Chara + Yogini + Ashtottari + Kalachakra).
- `v6.0.11` — Shadbala internal invariant validation (1200/1200 pass); downgraded to `partial`.

### Actively Working On (P0)

1. **Chara Dasha rewrite** — align with PyJHora KN Rao method (target: ≥95% match)
2. **Shadbala external calibration** — align with JHora / PyJHora / BV Raman
3. **Darakaraka / RTN external benchmark** — v6.1.10 has wired the modules; next step is traditional case validation and evidence ranking
4. **KP Sub-Lord full implementation** — unequal Vimshottari subdivisions
5. **Bhava Chalit complete** — cusp-based planet reassignment
6. **Sudarshana Chakra traditional** — Sun/Moon/Lagna reference points

### Next (P1)

- Benchmark harness (PyJHora output comparison)
- English documentation completion
- Docker image
- MCP Server endpoint
- GitHub Actions CI

---

## Development

### Running the Test Suite

```bash
# Syntax check all scripts
python3 -m py_compile scripts/*.py

# Capability audit (must pass with 0 problems, 0 warnings)
python3 scripts/audit_capabilities.py --mode validate

# Full-reading regression test (use FICTIONAL data only)
python3 scripts/jyotish_engine.py full-reading \
  --year 1990 --month 6 --day 15 \
  --hour 10 --minute 30 \
  --lat 39.9042 --lon 116.4074 --tz 8 \
  --age 36 \
  --transit-date 2026-06-04
```

### Important Rules

1. **NEVER** put real user birth data into skill files, tests, CHANGELOG, or public repos
2. Use only: (a) public AA-rated celebrity data, (b) explicitly fictional smoke tests, (c) current-session data (never persisted)
3. Always run `git status --short --branch` before starting work
4. Always run `py_compile` + `audit_capabilities.py` + full-reading regression after modifications
5. Do NOT upgrade `partial` to `covered` without external benchmark evidence
6. Do NOT refactor arbitrarily; make minimal verifiable changes

### Directory Structure

```
jyotish-vedic-astrology/
├── SKILL.md                          # Core entry point (Chinese)
├── README.md                         # This file (English)
├── CHANGELOG.md                     # Version history
├── requirements.txt                  # Python dependencies
├── references/
│   ├── technique_registry.json      # Machine-readable technique registry
│   ├── strict-workflow-router.md   # Question-type routing rules
│   ├── quick-reference-guide.md    # Quick reference
│   └── ...                         # Knowledge reference docs
├── scripts/
│   ├── jyotish_engine.py           # Main engine entry point
│   ├── audit_capabilities.py       # Capability audit tool
│   ├── shadbala.py                # Shadbala implementation
│   ├── dasha_calculator.py        # Dasha calculations
│   └── ...                        # 30+ technique scripts
└── tests/                          # Test cases
```

---

## Contributing

We welcome contributions, especially:

1. **Benchmark data** — PyJHora / JHora output comparisons for specific techniques
2. **Traditional text verification** — checking technique implementations against BPHS, PVN Rao, BV Raman
3. **Documentation** — English docs, tutorials, example outputs
4. **Engineering** — Docker, CI, MCP Server, API layer
5. **Test cases** — fictional birth data with expected outputs

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b fix/chara-dasha-benchmark`)
3. Make your changes (follow the development rules above)
4. Run the full test suite
5. Commit with a clear message
6. Push and create a Pull Request

### Philosophy

We prioritize **truth over coverage**. It is better to have 10 well-benchmarked techniques than 50 poorly-implemented ones. If you contribute a technique, please include:
- The source text / authority it is based on
- Benchmark comparison data (if available)
- Honest assessment of limitations

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **Swiss Ephemeris** — astronomical calculation foundation
- **PyJHora** (`naturalstupid/PyJHora`) — benchmark reference for traditional algorithms
- **VedAstro** (`VedAstro/VedAstro`) — engineering and productization reference
- **BPHS (Brihat Parashara Hora Shastra)** — canonical text
- **PVN Rao / KN Rao** — traditional Jyotish teaching lineage

---

## Contact & Support

- **Issues:** [GitHub Issues](https://github.com/732642856/yinduzhanxing/issues)
- **Discussions:** [GitHub Discussions](https://github.com/732642856/yinduzhanxing/discussions)

---

> **Final note:** This system is a research tool. It should NOT be used for making life-altering decisions without consulting qualified human astrologers. The techniques implemented here are complex and context-dependent; software output always benefits from human judgment.
