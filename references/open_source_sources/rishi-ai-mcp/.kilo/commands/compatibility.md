---
description: Ashtakoot Compatibility Analysis Between Partners
---

# Compatibility Analysis Workflow

When the user wants to analyze relationship compatibility between two partners, execute these steps:

## Steps

1. **Gather Both Birth Details**:
   - Male: DOB, Time, Lat, Lon
   - Female: DOB, Time, Lat, Lon
   - Confirm Person 1 = Male, Person 2 = Female (traditional Ashtakoot)

2. **Fetch Compatibility Data**: Call `calculate_compatibility` with both sets of birth parameters.

3. **Read 8 Ashtakoot Kutas** (36 points total):
   - Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi
   - Each kuta has specific weights; sum gives total compatibility score

4. **Extra Kutas**: Read additional factors:
   - Mahendra: Nakshatra durability — same group nakshatras strengthen bond
   - Rajju: Nakshatra element mismatch — affects longevity
   - Stree Deergha: Female specific — affects offspring hope
   - Vedha: Nakshatra blocking — can impede relationship
   - Bad Constellations: Specific nakshatras that clash

5. **Exception Logic**: Check if any Nadi/Rajju exceptions apply that mitigate afflictions.

6. **Kuja Dosha Analysis**: 
   - Mars in houses 2, 4, 7, 8, 12 for both partners
   - Scoring based on dignity and house placement
   - Mild/Moderate/Severe verdict

7. **Synthesize & Deliver**:
   - **Overall Score**: X/36 with grade (Excellent/Good/Fair/Poor)
   - **Strength Areas**: Which kutas are favorable
   - **Challenge Areas**: Which kutas need remedy work
   - **Kuja Dosha Status**: If present, severity and remedies
   - **Exception Benefits**: If exceptions apply, how they help
   - **Timing**: When favorable periods activate based on dasha
   - **Remedies**: Sattvic remedies for weak kutas

## Tools
- `calculate_compatibility`: 36-point Ashtakoot + Kuja Dosha + extra kutas
