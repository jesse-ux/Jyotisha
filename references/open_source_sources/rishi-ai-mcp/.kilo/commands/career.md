---
description: Career and Professional Analysis using D10 Dashamsha
---

# Career Analysis Workflow

When the user wants career guidance, professional path analysis, or dasha-based career timing, execute these steps:

## Steps

1. **Gather Birth Details**: DOB, Time, Lat, Lon.

2. **Fetch Chart Data**: Call `cast_vedic_chart` first for foundational data.

3. **Analyze Career Chart**: Call `analyze_career_chart` for D10 Dashamsha deep dive.

4. **Read 10th House (Karma Sthana)**:
   - Lord of 10th house: its sign, house, dignity
   - Occupants of 10th: planets placed there
   - `d10_sign` of lord and occupants

5. **D10 Planetary Indicators**: For each planet in D10:
   - Read `d10_sign` and `career_domain` significations
   - Identify which planets are well-placed for career expression

6. **Career Themes**: Read `career_themes` (ranked array) for primary and secondary career directions.

7. **Strength Factors**: Check 6th/7th lord connections to 10th — indicates entrepreneurship vs employment倾向.

8. **Cross-Reference with Natal**:
   - Atmakaraka's house/sign — career calling
   - Amatyakaraka's placement — professional orientation
   - Saturn's dignity and house — work discipline and longevity

9. **Dasha Timing**: Use `dashas.timeline` to identify upcoming periods favorable for:
   - Career changes
   - New job opportunities
   - Promotions
   - Entrepreneurship moves

10. **Synthesize & Deliver**:
    - **Career Archetype**: Primary professional identity
    - **Strengths**: Natural talents and planetary supports
    - **Challenges**: Areas needing development or facing delays
    - **Ideal Environments**: Work settings that favor the native
    - **Timing Forecast**: When to expect major career shifts
    - **Remedies**: Career-enhancing Sattvic practices

## Tools
- `cast_vedic_chart`: Foundation data (call first)
- `analyze_career_chart`: D10 Dashamsha career analysis (call second)
