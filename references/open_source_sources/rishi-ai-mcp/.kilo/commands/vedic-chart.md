---
description: Full Vedic Natal Chart Reading
---

# Vedic Chart Reading Workflow

When the user wants a complete Vedic (Jyotish) natal chart reading, execute these steps:

## Steps

1. **Gather Birth Details**: Ask for DOB (DD/MM/YYYY), Time of Birth (HH:MM), Place of Birth (for lat/lon/timezone), Gender, and their specific question.

2. **Geocode Place**: Convert birth city to lat/lon/timezone. Key references:
   - Delhi: 28.6139, 77.2090, Asia/Kolkata
   - Mumbai: 19.076, 72.8777, Asia/Kolkata
   - Bangalore: 12.9716, 77.5946, Asia/Kolkata
   - New York: 40.7128, -74.006, America/New_York
   - London: 51.5074, -0.1278, Europe/London

3. **Fetch Chart Data**: Call `cast_vedic_chart` with birth parameters.

4. **Read Key Indicators**:
   - `panchang`: tithi, vara, nakshatra, yoga, karana
   - `lagna.sign`, `lagna.nakshatra` — core personality framework
   - `shadbala.percentage` for each planet (>100% = exceptionally strong, <80% = weak)
   - `shadbala.ishta_kashta_phala` — auspicious vs difficult potential
   - `dignity`, `is_combust`, `is_retrograde` — modifier flags
   - `avasthas` — Yuva = full delivery, Bala/Mrita = diminished

5. **Jaimini Karakas**: Read `jaimini_karakas`. Atmakaraka = soul lesson; Amatyakaraka = career direction.

6. **House-Lord-Karaka**: Use `house` field for bhava placement. Cross-reference lordship from Lagna.

7. **Vargas**: D2 (wealth), D9 (marriage), D10 (career), D16 (luxuries), D20 (spirituality), D60 (past-life karma).

8. **Yogas**: READ from `yogas` array — don't detect manually. Assess dignity + combustion of forming planets.

9. **Dashas**: Read all 5 levels (Maha/Antar/Pratyantar/Sukshma/Prana) + `dashas.timeline`.

10. **Synthesize & Deliver Reading**:
    - **Core Essence**: Lagna + Moon + Panchang + dominant yogas
    - **Current Vibe**: Dasha snapshot + transits + Sade Sati
    - **Detailed Analysis**: House + Lord + Karaka framework
    - **Yoga Impact**: Each detected yoga: promise, strength, timing
    - **Probable Outcomes**: Descending probability
    - **Diagnostic Questions**: 1-3 data-driven probing questions
    - **The Key**: Lifestyle shift + spiritual remedy + timing

## Tools
- `cast_vedic_chart`: Primary tool — call FIRST
- `cast_transit_chart`: Call AFTER natal chart for current influences
