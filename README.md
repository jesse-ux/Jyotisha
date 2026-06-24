# Jyotish Vedic Astrology — AI-Native Full-Reading System

> **What makes this different:** This is not a calculator. It is an AI-native Jyotish analysis system that combines calculation engines, interpretive workflows, confidence auditing, and graceful degradation — organized into a reproducible full-reading pipeline.

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Techniques](https://img.shields.io/badge/techniques-65-blueviolet)](references/technique_registry.json)
[![Covered](https://img.shields.io/badge/covered-55-green)](references/technique_registry.json)
[![Complete](https://img.shields.io/badge/complete-10-brightgreen)](references/technique_registry.json)
[![Partial](https://img.shields.io/badge/partial-0-lightgrey)](references/technique_registry.json)

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
2. **Runs** 65 registered techniques (Dashas, Yogas, Shadbala, Ashtakavarga, Transits...)
3. **Routes** the analysis through strict workflow paths depending on question type (career / relationship / wealth / timing)
4. **Audits** every technique used — declaring what was called, what is complete/covered, and which limitations affect confidence
5. **Degrades gracefully** — limitations are labeled, not silently over-promising

### Key Differentiators (vs. PyJHora / VedAstro / Maitreya)

| Feature | This Project | PyJHora | VedAstro | Maitreya |
|---------|-------------|----------|----------|----------|
| Full-reading pipeline (one command) | ✅ | ❌ | ❌ | ❌ |
| Strict workflow router (per-question-type) | ✅ | ❌ | ❌ | ❌ |
| Technique Audit Table (confidence labeling) | ✅ | ❌ | ❌ | ❌ |
| Capability degradation (limits are explicit) | ✅ | ❌ | ❌ | ❌ |
| MEVG external verification gates | ✅ | ❌ | ❌ | ❌ |
| 65 techniques registered | ✅ | ✅ (50+) | ✅ (200+) | ✅ |
| Traditional algorithm benchmarked | ✅ mixed depth | ✅ | ✅ | ✅ |
| Docker / MCP Server | ✅ | ❌ | ✅ | ❌ |
| English docs / PyPI package | ✅ in progress | ✅ | ✅ | ✅ |

---

## Quick Start

### 普通用户启动路径

如果只是打开网页/app，请按同一条路径走，不要在多个入口之间猜：

1. 先启动网页服务：cd jyotish-app && npm run dev -- --host 127.0.0.1 --port 5173
2. 再启动本地 API 服务：python3 scripts/jyotish_api_server.py --host 127.0.0.1 --port 5200
3. 打开 Trust Center，点击运行健康检查；页面地址是 `http://127.0.0.1:5173`。
4. 如果只安装 PWA：PWA 安装壳只包装网页服务，本地 API 服务仍需单独启动；无 API 时网页会保留基础浏览器 fallback，但 PDF/高级技法需要本地 API 服务。
5. 开发者做完整自检时运行：`python3 scripts/run_quality_gate.py --frontend-click-timeout 240`。

### 质量门分层

- quick：快速开发守门，适合普通代码/文案修改后先跑：`python3 scripts/run_quality_gate.py --profile quick`
- browser：完整浏览器守门，覆盖 runtime smoke 与真实浏览器用户路径：`python3 scripts/run_quality_gate.py --profile browser`
- release：发布前守门，包含关键产品文件未跟踪检查、慢速 golden cases 与 Yoga 逻辑报告：`python3 scripts/run_quality_gate.py --profile release`

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
[✓] Shadbala (covered — internally consistent; external absolute calibration still capped)
[✓] Yogas & Doshas
[✓] Argala (planetary interventions)
[✓] Nakshatra Advanced (Chandra Bala / Tara Bala)

── Dynamic Timing ──
[✓] Vimshottari Dasha breakdown
[✓] Dasha Sandhi detection
[✓] Transit (true positions)
[✓] Double Transit analysis
[✓] Narayana Dasha
[✓] Solar Return / Varshaphala
[✓] Nakshatra Dasha (Ashtottari)

── Technique Audit Table ──
✓ Vimshottari Dasha        covered      high confidence
✓ Ashtakavarga             covered      high confidence
✓ Shadbala                covered      internal invariant benchmark passed; absolute calibration capped
✓ Chara Dasha             covered      KN Rao benchmark 95.83% overall match
✓ KP Sub-Lord             covered      SubLord/SubSubLord + ABCD significator workflow
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

Current count: **65 techniques** (55 covered, 10 complete, 0 partial, 0 missing)

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
| Nakshatra Advanced | ✅ covered | Tara Bala / Chandra Bala / Sub-Lord workflow |
| Narayana Dasha | ✅ covered | CLI and full-reading integration |
| Solar Return / Varshaphala | ✅ covered | Tajika annual-chart workflow |
| **Shadbala** | ✅ covered | **1200/1200 internal invariants pass; external absolute-value calibration remains a confidence cap** |
| **Chara Dasha** | ✅ covered | **KN Rao benchmark: sign 100%, duration 91.67%, overall 95.83%** |
| KP Sub-Lord | ✅ covered | SubLord/SubSubLord + ABCD significator workflow |
| Bhava Chalit | ✅ covered | Sripati/Porphyry/Equal/Whole Sign/Placidus/Koch |
| Sudarshana Chakra | ✅ covered | Asc/Moon/Sun reference charts + convergence scoring |
| Tajika Yogas | ✅ complete | Annual-chart yoga set |
| Raj Yoga | ✅ covered | Rule-based detection |
| Dhana Yoga | ✅ covered | Rule-based detection |
| Pancha Mahapurusha | ✅ covered | Complete detection |
| Neecha Bhanga | ✅ complete | Debilitation cancellation workflow |
| Sade Sati | ✅ covered | Saturn pressure timing |
| Tithi Lord | ✅ complete | Lunar-day ruler workflow |
| Pancha Pakshi | ✅ complete | Five-bird system |
| Rashi Tulya Navamsa | ✅ covered | D1/D9 mapping |
| Trimshamsa D30 | ✅ covered | D30 varga support |
| Marriage Counting | ✅ complete | Bhrigu Pada marriage-counting method |
| Prashna Integration | ✅ complete | Prashna workflow integrated |
| Bhrigu Pada Dasha | ✅ complete | Pada progression workflow |
| Muhurta | ✅ covered | Panchanga / auspicious timing workflow |

**Legend:**
- ✅ `covered` — implemented and benchmarked against authoritative sources
- ✅ `complete` — implemented with integrated workflow and validation hooks
- ✅ `covered` — implemented and available in the engine, sometimes with explicit confidence caps
- 🔶 `partial` — reserved for implemented-but-insufficiently-integrated techniques; current registry count is 0
- ❌ `missing` — not currently present in the registry; current registry count is 0

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
3. **Degrading gracefully** — confidence caps and limitations are labeled, not silently over-promising
4. Being **AI-native** — designed for integration with LLM-based analysis

---

## Honest Assessment

We believe in transparency about limitations. This is NOT a "99% accurate" system, and anyone claiming that about Jyotish is over-selling.

### Current Accuracy Estimates (self-evaluated)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Astronomical foundation (Swiss Eph) | 8.5/10 | Depends on ayanamsa, node mode, house system |
| Traditional algorithm accuracy | 8.1/10 | Chara Dasha benchmark passed; Shadbala still needs external absolute-value calibration |
| Technique coverage breadth | 9.1/10 | 65 registered techniques; broad and increasingly benchmarked |
| Reading detail depth | 9.6/10 | Possibly best among open-source projects |
| Prediction workflow rigor | 8.8/10 | Strict routing + audit table |
| Verification system | 8.2/10 | Has registry, benchmark, degradation; some verification still internal |
| Engineering maturity | 7.6/10 | Docker, PyPI config and CI exist; release artifacts still need cleanup |
| Open-source influence | 5.5/10 | Currently more of a "private high-density toolkit" |

### What Confidence Caps Mean (Important)

Even when a technique is labeled `covered`, it may carry a confidence cap:
- It CAN produce output
- Some components may still need external absolute-value calibration against PyJHora / JHora / canonical texts
- It should be interpreted together with cross-technique evidence
- It must NOT be the sole basis for high-confidence predictions when its limitation says so

Examples:
- `Shadbala` (covered with cap): Internal invariants pass (1200/1200). External absolute values are not fully calibrated, so use primarily for relative strength ranking.
- `Chara Dasha` (covered): KN Rao benchmark passes at 95.83% overall; remaining differences are documented around Aquarius/Scorpio co-lord strength arbitration.

---

## Project Status

**Current version:** `v6.9.14`

### Recently Completed

- `v6.9.14` — Sudarshana Chakra complete + 475 pytest cases + 65-technique registry audit PASS.
- `v6.9.13` — Bhava Chalit complete + transit trigger output normalization + Nakshatra test calibration.
- `v6.9.12` — Shadbala precision upgrade + Ashtakoot 36-point compatibility + expanded subcommands.
- `v6.9.6` — Field mapping fixes (degree→degree_in_sign + toFixed null safety); PyPI publishing config.
- `v6.9.5` — birth_info null safety + API field mapping fixes.
- `v6.9.4` — AI interpretation integration; current browser build disables direct model API keys and routes AI through server-side `/api/chat` or a backend proxy.
- `v6.9.3` — 35 Dasha systems, 405+ Yoga rules, KP complete system, Prashna, 16-factor synastry, Remedies, Sahams 36, Sudarshana, PMC, Tajika.
- `v6.1.12` — Chara Dasha KN Rao Method rewrite, PyJHora benchmark 95.83% PASS.
- `v6.1.10` — Darakaraka deep reader wired into `full-reading.modules.jaimini.darakaraka`; thematic reports now consume real DK and Rashi Tulya Navamsa evidence.
- `v6.1.9` — Public/sanitized benchmark suite, competitive research, coverage roadmap and PDF validation methodology added.
- `v6.1.8` — Yoga validation reached F1=95.22% (FP=36, FN=63); thematic reports consume real `full-reading.modules` evidence.
- `v6.1.6` — Five-system Dasha convergence wired into full-reading (Vimshottari + Chara + Yogini + Ashtottari + Kalachakra).
- `v6.0.11` — Shadbala internal invariant validation (1200/1200 pass); later upgraded to covered with explicit calibration cap.

### Actively Working On (P0)

1. **Release hygiene** — run the release profile, keep product-critical files tracked, rebuild wheel/sdist, and align GitHub tags with source version
2. **README / package metadata sync** — keep public docs, registry counts and distribution artifacts consistent
3. **Shadbala external absolute calibration** — align full tables with JHora / PyJHora / BV Raman
4. **Benchmark expansion** — add more oracle cases for Vimshottari, Shadbala, KP and annual-chart modules
5. **Frontend verification** — keep the pure JS/WASM fallback aligned with the Python engine output

### Next (P1)

- Docker image publishing and smoke-test docs
- English documentation examples and API tutorials
- Multi-Ayanamsa UX polish and benchmark examples
- Desktop packaging path: PWA now, Pake URL shell for quick wrappers, Tauri sidecar after API lifecycle/signing decisions. See `docs/research/desktop_packaging_spike_2026_06_23.md`.

---

## Development

### Running the Test Suite

```bash
# Syntax check all scripts
python3 -m py_compile scripts/*.py

# Capability audit (must pass with 0 problems, 0 warnings)
python3 scripts/audit_capabilities.py --mode validate

# Desktop packaging readiness
python3 scripts/desktop_packaging_preflight.py

# Installed-shell / first-launch browser smoke
python3 tests/run_frontend_click_smoke.py --mode all

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
5. Do NOT remove a confidence cap without external benchmark evidence
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
│   └── ...                        # 90+ technique and orchestration scripts
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
