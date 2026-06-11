---
description: Past Life & Karmic Debt Analysis Workflow
---
# Past Life Analysis Workflow

When performing a past life and karmic analysis, execute the following steps:

1. **Fetch Chart Data**: Call `cast_vedic_chart` (birth parameters only — no transit needed for past life analysis).

2. **Ketu — The Past Life Signature Planet**:
   - Read Ketu's `house`, `sign`, `nakshatra`, and `nakshatra_lord` from the natal chart. These are the most direct indicators of the past life scenario.
   - Ketu's **house** = the area of soul mastery (and over-reliance) carried from the previous incarnation.
   - Ketu's **nakshatra** = the specific texture and story of the past life.
   - Ketu's **nakshatra_lord** placement in the D1 chart = how the past-life memory is actively affecting the native now.
   - Conjunctions with Ketu: any planet sitting with Ketu is "karmic," past-life flavored — its significations dominated the previous life.

3. **Rahu — The Karmic Frontier (This Life's Direction)**:
   - Rahu's house and nakshatra reveal the direction the soul must consciously move toward in this incarnation — the evolutionary antidote to Ketu's over-mastered past.
   - Assess the Rahu-Ketu axis as a whole: the polarity tells the full story of what was and what must become.

4. **Atmakaraka (Karmic King of the Chart)**:
   - From `jaimini_karakas`, identify the Atmakaraka — the soul's single most critical karmic lesson for this birth.
   - Check its `dignity`, `is_retrograde`, `is_combust`, `avasthas`, and `shadbala.percentage`.
   - If retrograde/debilitated/combust/Mrita Avastha: the soul arrives with heavy unfinished business — this lesson is non-negotiable and front-loaded into life experience.

5. **Karakamsha (Soul Blueprint from Previous Lives)**:
   - Read `karakamsha` directly — the AK's D9 Navamsha sign and planets placed in it reveal the core soul identity and orientation carried from past incarnations.
   - Each planet in the Karakamsha sign = a past-life preoccupation (e.g., Mars = past warrior, Ketu = past monk, Jupiter = past scholar, Saturn = past ascetic/servant).

6. **D60 (Shashtiamsha) — The Finest Karmic Record**:
   - Read `d60_sign` for every planet. This is the deepest indicator of past-life karma in the varga system.
   - Exalted planets in D60 = karmic graces, virtues, or mastery brought forward. Debilitated planets in D60 = karmic wounds being reworked. The Atmakaraka's D60 sign is the most critical.

7. **5th House (Purva Punya — Past-Life Merit)**:
   - Analyze the 5th house, its lord, and occupants. Benefics + strong 5th lord = rich past-life merit. Afflictions = karmic debt or insufficient merit — this life requires more effort.
   - Ketu in the 5th = strong past spiritual practice; Rahu in the 5th = past life misuse of intelligence or creative gifts.

8. **12th House (Karmic Exit & Residue)**:
   - Analyze the 12th house and its lord. Planets here carry unresolved energy from the last life's end. The 12th lord's placement reveals what domain was left incomplete.

9. **Saturn (The Karmic Accountant)**:
   - Saturn's house and sign reveal where the soul is repaying its most stubborn karmic debt through delay, discipline, and hardship.
   - Check `is_retrograde` (past-life pattern being re-run), `dignity` (debilitated = severe debt, possibly multi-incarnation), and `shadbala.kashta_phala` (weight of karmic burden).

10. **Retrograde Planets**:
    - Flag all planets where `is_retrograde: true`. Each is a soul-contract from a past life being replayed or completed. Assess the houses they rule and occupy — those house significations carry past-life unfinished business.

11. **Yogas of Karmic Significance**:
    - Flag `Viparita Raj Yoga` (deliberate hard path chosen by soul), `Neecha Bhanga Raj Yoga` (a past-fallen planet rising again), and `Parivartana Yoga (Dainya)` (complex karmic entanglements between dusthana houses).

12. **Synthesize — The Past Life Story**:
    Weave all data into a coherent, empathetic narrative covering:
    - **Who the soul was** (Ketu + Karakamsha)
    - **What was mastered** (Ketu's house, D60 exaltations, strong 5th)
    - **What was left unresolved** (12th house planets, retrograde planets, debilitated D60 planets)
    - **What debt is being paid** (Saturn's house/dignity, Kashta Phala weight)
    - **What this life is for** (Rahu's direction + Atmakaraka's lesson)
    - **Remedies**: Mantra for AK planet, seva for Saturn's afflicted house, meditation for Ketu nakshatra deity, timing tied to current Dasha activation.
