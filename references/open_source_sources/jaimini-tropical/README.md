# Jaimini Tropical Astrology Engine

A high-precision **Jaimini astrology** computation engine using the **Tropical Zodiac** (Sayana). Built from scratch based on Iranganti Rangacharya's authoritative works — *Jaimini Sutramritam* and *Jyotish-Prasana*.

**Key differentiator**: All existing Jaimini/Vedic libraries use the Sidereal zodiac (Lahiri Ayanamsa). This is the first engine built for the **Tropical zodiac**, making Jaimini techniques compatible with classical Western astrology (Hermetic Lots, etc.).

## Design Principles

1. **Purely Jaimini** — No Parashara/BPHS contamination. No Vimshottari Dasha, no Shadbala, no planetary aspects. Jaimini is treated as a self-contained, independent system per Iranganti Rangacharya's teachings.

2. **Tropical (Sayana)** — Default tropical zodiac for compatibility with classical Western techniques. No ayanamsa applied.

3. **Whole Sign Houses** — Per Brhat Jataka 1.4: Rasi = Bhava. One sign = one house.

4. **High Precision** — NASA JPL DE421 ephemeris via Skyfield. Sun position accurate to <1 arcsecond, Moon to <10 arcseconds.

5. **Data over Graphics** — Output is precise numerical tables, not visual chart wheels. Every calculation is transparent and reproducible.

## Features

### Layer 1: Planetary Positions (JPL DE421)
- All 7 classical planets + Rahu/Ketu + outer planets
- Tropical longitude to 6 decimal places
- Speed (deg/day), retrograde detection, ecliptic latitude

### Layer 2: Chara Karaka & Arudha Pada
- **7 Chara Karakas** (Atmakaraka through Darakaraka) by degree-within-sign ranking
- **12 Arudha Padas** (A1-A12) with standard exception rules
- **Upapada** (UL) for spouse analysis

### Layer 3: Special Lagnas (Ghati-based time differentiation)
- **Hora Lagna** (HL / Yin-Yang Fortune) — ~1 hour sensitivity
- **Ghatika Lagna** (GL / Five-Element Fortune) — 24 minute sensitivity
- **Varnada Lagna** (VL / Palace Origin) — derived from Ascendant

### Layer 4: Divisional Charts
- **D-9 Navamsa** — Jaimini's Yang-forward/Yin-reverse mapping
- **D-3 Drekkana** — Parivrittitraya method
- **D-12 Dwadashamsha**

### Argala Analysis (Jaimini Judgment System)
- Primary Argala (houses 2, 4, 11) — positive planetary intervention
- Virodhargala obstruction (houses 12, 10, 3)
- Specific Argala (house 3 with 2+ malefics)
- Secondary Argala (houses 5, 9)
- Argala Rajayoga classification (Poorna/Tripada/Ardha/Padargala)
- Karakamsa Rajayoga (AK in Navamsa analysis)

### Chara Dasha (Variable-Period System)
- Full 12-sign Mahadasha timeline from birth
- Prakriti Chakra sign sequence
- Antar (Bhukti) sub-periods with proportional year distribution

## Quick Start

```bash
pip install skyfield numpy
python run_jaimini.py "1949-10-01" "15:00:00" "+8" "39.907" "116.397"
```

### Input Format
```
python run_jaimini.py <date> <time> <timezone> <latitude> <longitude> [options]

Options:
  --name, -n          Chart name/label
  --house-system, -hs House system: W=Whole Sign (default), P=Placidus, E=Equal
  --include-rahu, -r  Use 8-karaka system (includes Rahu)
  --dasha-only, -d    Show only Dasha timeline
  --karakas-only, -k  Show only Karaka assignments
  --output, -o        Save output to file
```

### Examples

```bash
# New China chart (Beijing, 1949-10-01 15:00 CST)
python run_jaimini.py "1949-10-01" "15:00:00" "+8" "39.907" "116.397" --name "New China"

# DMS format coordinates
python run_jaimini.py "2025-06-15" "06:30:00" "+5.5" "28°36′50″" "77°12′30″" --dasha-only

# Save full analysis to file
python run_jaimini.py "1949-10-01" "15:00:00" "+8" "39.907" "116.397" -o chart.txt
```

## Project Structure

```
jaimini/
├── engine/              # Astronomical engine (Skyfield/JPL DE421)
│   ├── ephemeris.py     # Planetary positions — tropical
│   ├── houses.py        # Whole Sign / Placidus houses + sunrise
│   └── time_utils.py    # Julian Day, DMS conversion, timezone
├── core/                # Jaimini-specific calculations
│   ├── karakas.py       # Chara Karaka (7-planet system)
│   ├── dashas.py        # Chara Dasha + Antar/Bhukti
│   ├── padas.py         # Arudha Pada (A1-A12, Upapada)
│   ├── lagnas.py        # HL, GL, VL special lagnas
│   ├── divisions.py     # Jaimini D-9, D-3, D-12
│   └── argala.py        # Argala/Virodhargala + Rajayoga
├── chart/               # Chart integration
│   └── chart.py         # Chart object (all calculations)
├── cli/                 # Command-line interface
│   └── main.py
├── tests/               # Validation tests (31/31 passing)
│   ├── test_engine.py   # Astronomical accuracy tests
│   └── test_jaimini.py  # Jaimini calculation tests
└── run_jaimini.py       # Entry point
```

## Accuracy

| Measurement | Accuracy | Verification |
|-------------|----------|-------------|
| Sun longitude | <0.002° (~7 arcsec) | Swiss Ephemeris swetest64.exe |
| Moon longitude | <0.01° (~36 arcsec) | Swiss Ephemeris swetest64.exe |
| DE421 vs DE431 | ~0.5 arcsec (Sun) | JPL ephemeris version difference |

Reference: 1949-10-01 07:00 UTC chart verified against official swetest64.exe output.

## Sources

- **Iranganti Rangacharya**, *Jaimini Sutramritam* (Translation and Commentary in English)
- **Umang Taneja**, *Jyotish-Prasana: A Contemporary Treatise Using KP Prasna*
- **Skyfield** — NASA JPL DE421 ephemeris (MIT licensed)
- **dashaflow** — Algorithm reference for Arudha Pada and Karakamsa (MIT licensed)

## License

MIT License — see LICENSE file.

## Running Tests

```bash
python -m jaimini.tests.test_engine     # 13 tests: planetary accuracy, houses, time
python -m jaimini.tests.test_jaimini    # 18 tests: karakas, dashas, padas, argala
```
