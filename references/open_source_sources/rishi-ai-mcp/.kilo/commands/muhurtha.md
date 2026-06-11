---
description: Electional Astrology — Find Auspicious Time for Activity
---

# Muhurtha (Electional Astrology) Workflow

When the user wants to find the best time for an important activity (marriage, travel, business, education, house entry, medical), execute these steps:

## Steps

1. **Confirm Activity Type**: Must be one of:
   - `marriage` — wedding Muhurtha
   - `travel` — journey Muhurtha
   - `business` — new venture, signing
   - `education` — starting studies, exams
   - `house_entry` — grihapravesha
   - `medical` — surgery, treatment

2. **Gather Parameters**: Date range, Time (if specific), Location (Lat, Lon, Timezone).

3. **Fetch Muhurtha Data**: Call `check_muhurtha_tool` with activity type and parameters.

4. **Read Verdict**: 
   - `auspicious`: Full green light — all factors favorable
   - `mixed_favorable`: Mostly good with minor considerations
   - `mixed`: Caution needed — weigh pros and cons
   - `inauspicious`: Avoid or reschedule if possible

5. **Score Analysis**: Read `score` (positive×10 - negative×15). Higher = better.

6. **Positive/Negative Factors**: Parse specific reasons for verdict.

7. **Panchang Suddhi**: Check tithi, vara, nakshatra, yoga, karana purity.

8. **Marriage-specific**: If `marriage` activity, also read:
   - Sagraha — planetary alliance check
   - Shashtashta — 60th part of both luminaries
   - Bhrigupta Shatka — Bride's Mars placement analysis
   - Kujaasthama — Mars position severity

9. **Synthesize & Deliver**:
   - **Verdict**: Clear recommendation
   - **Best Time**: Specific date/time if score is favorable
   - **Positive Factors**: What's working in your favor
   - **Negative Factors**: What to be aware of
   - **Remedies**: Any pujan, charities, or mantras to strengthen the Muhurtha
   - **Alternative**: If current date is poor, suggest better date range

## Tools
- `check_muhurtha_tool`: Electional astrology for 6 activity types
