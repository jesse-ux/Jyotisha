---
description: Current Planetary Transit Analysis
---

# Transit Analysis Workflow

When the user wants to know current planetary transits and their influence on the natal chart, execute these steps:

## Steps

1. **Confirm Natal Data**: Ensure you have DOB, Time, Lat, Lon from previous `/vedic-chart` call.

2. **Fetch Transit Data**: Call `cast_transit_chart` with today's date and natal birth parameters.

3. **Read Transit Indicators**:
   - Each planet's `sign`, `degree`, `nakshatra`, `sav_points`
   - `house_from_lagna` and `house_from_moon` forastro-weather interpretation
   - `sav_points` ≥ 28 = easy results; < 25 = struggle

4. **Sade Sati Check**: Read `sade_sati` — Saturn's 7.5-year transit over Moon sign. Active phases indicate karmic intensification.

5. **Rahu-Ketu Axis**: Read `rahu_ketu_axis` — the nodal axis being activated reveals karmic churning in specific life areas.

6. **Ashtakavarga Transit Points**: Use `prashtarashtakavarga` to see which specific planets contribute bindus (good effects) to transiting signs.

7. **Synthesize Transit Report**:
   - Identify which planets are transiting each house
   - Note conjunctions and aspects to natal planets
   - Flag high-bindhu transits (easy results) vs low-bindhu transits (challenging)
   - Map timing: which antar-dashas align with current transits

8. **Deliver Transit Reading**:
   - Current planetary weather per house
   - Which houses are activated and how
   - Key opportunities and challenges in next 3-6 months
   - Remedies if needed (Sattvic practices preferred)

## Tools
- `cast_transit_chart`: Always call AFTER `cast_vedic_chart`
