---
name: past-life-analysis
description: "Use when analyzing past life karma, karmic debts, soul's unfinished business, past life talents, or the karmic story carried into this birth."
---

# Past Life Analysis Workflow

TRIGGER: Use this skill when the user asks about past lives, karmic baggage, karmic debts, why they feel inexplicable pulls or aversions to places/people/fields, or what soul-level wounds they carry from past incarnations.

## Steps

1. **Fetch Chart Data**: Call `cast_vedic_chart` (birth parameters). This is the primary and sufficient tool — no transit data is needed for past life analysis.

2. **D60 (Shashtiamsha) — The Finest Karmic Record**:
   - Read `d60_sign` for **every planet**. The D60 is the finest divisional chart and the most direct window into past-life karma in BPHS tradition.
   - Planets in exaltation / own sign in D60 = karmic strengths brought forward (talents, graces, virtues).
   - Planets debilitated / in enemy signs in D60 = karmic wounds, debts, or patterns the soul is still working through.
   - Note the D60 sign of the Atmakaraka (AK) particularly — it reveals the soul's karmic entry point for this life.

3. **Atmakaraka (The Karmic King)**:
   - From `jaimini_karakas`, identify the Atmakaraka — the planet with the highest degree. It represents the soul's single most critical karmic lesson for this incarnation.
   - Its natal sign, house, dignity, `avasthas` strength, and `shadbala.percentage` reveal how easily or painfully this lesson is being confronted.
   - If Atmakaraka is debilitated, retrograde, combust, or in Mrita Avastha: the soul is arriving with a heavy backpack from a past life — unresolved karma is front-and-center.

4. **Karakamsha (Soul's Blueprint in Navamsha)**:
   - Read `karakamsha` directly. The AK's D9 sign (Karakamsha sign) and planets placed in it reveal:
     - The core soul-level orientation carried from past lives.
     - Planets in Karakamsha = past life preoccupations that continue into this life.
   - Mars in Karakamsha sign = past life soldier, warrior, or someone who lived by force/willpower.
   - Jupiter in Karakamsha = past life priest, scholar, or dharmic advisor.
   - Saturn in Karakamsha = past life servant, ascetic, or one who suffered through isolation.
   - Ketu in Karakamsha = past life yogi, monk, or intensely spiritual being — moksha was close.
   - Mercury in Karakamsha = past life merchant, communicator, or intellectual.
   - Venus in Karakamsha = past life artist, lover, or courtier — born with refined aesthetic sensibility.
   - Sun in Karakamsha = past life king, administrator, or figure of authority.
   - Moon in Karakamsha = past life caregiver, healer, or emotionally bound persona.

5. **Ketu — The Karmic Signature Planet**:
   - Ketu's natal house, sign, nakshatra, and nakshatra lord are the single most critical indicators of the past life.
   - **Ketu's House** = the area where the soul is already at mastery from past lives (and simultaneously the area it must detach from and not over-rely on in this life).
   - **Ketu's Sign** = the mode of existence in the most recent past life.
   - **Ketu's Nakshatra** = the texture and very specific story of the past life.
   - **Ketu's Nakshatra Lord** = the planet that "holds the memory" of the past life. Its current natal placement modifies how that memory affects the native.
   - If Ketu is conjunct a planet: that planet "belongs to the past" — its significations were dominant in the previous life and are karmic.
   - If Ketu is aspecting a house significantly: that house's significations carry past-life entanglements.

6. **Rahu — The Karmic Frontier (Dharmic Direction)**:
   - Rahu's house, sign, and nakshatra show the direction the soul must move *toward* in THIS life — the antidote to Ketu's past-life over-specialization.
   - The axis: Ketu = where you've been, Rahu = where you must go. The tension between them is the engine of the soul's evolution in this incarnation.

7. **5th House (Purva Punya — Past Merit)**:
   - The 5th house and its lord reveal the merit (punya) accrued in past lives through righteous deeds, devotion, or spiritual practice.
   - A strong 5th lord (`shadbala.percentage` > 100%) + benefics = rich past-life merit — this life flows more easily.
   - A weak/afflicted 5th = karmic debt or insufficient past-life credit — this life requires extra effort and self-building.
   - Ketu in the 5th = strong past-life spiritual practice but possible disconnection from creative joy in this life.

8. **12th House (The Exit Point of the Previous Life)**:
   - The 12th house shows the circumstances and energetic theme of the previous life's end, as well as the karmic residue of that transition.
   - Planets in the 12th house carry "unresolved business" from the last incarnation.
   - The 12th lord's placement reveals what domain of life was left incomplete.

9. **Saturn (The Karmic Accountant)**:
   - Saturn's house and sign reveal the area of the heaviest karmic debt and the domain where the soul is being made to pay back old dues through discipline, delay, and hard work.
   - Retrograde Saturn = the soul is re-running a karmic scenario it did not resolve in the previous birth. There is a distinct "Groundhog Day" quality to that house's themes.
   - Debilitated Saturn = the debt is severe; the soul has avoided this lesson for multiple incarnations. This life is non-negotiable resolution time.
   - Saturn's `shadbala.ishta_kashta_phala` (Kashta Phala) reveals the weight of the karmic burden it represents.

10. **Retrograde Planets**:
    - Every retrograde planet (noted by `is_retrograde: true`) is a soul-contract carried from a past life. Its significations are being "redone" or "completed" — they have an inward, past-life flavor.
    - Retrograde benefics (Jupiter, Venus): spiritual wisdom or relationships that were developed in a past life and are being further refined.
    - Retrograde malefics (Saturn, Mars): past-life aggression, injustice, or karmic confrontations that must be resolved.

11. **Yogas with Karmic Significance**:
    - Note `Viparita Raj Yoga` — formed from dusthana lords — this yoga often indicates the soul has chosen a hard path deliberately for spiritual growth.
    - `Neecha Bhanga Raj Yoga` = a planet that fell/failed in a past life rises again with grit and grace in this one.
    - `Parivartana Yoga (Dainya)` = planetary exchange involving a dusthana — signals complex karmic entanglements between the significations of those two houses.

12. **Synthesize — The Past Life Story**:
    From all the above, paint a coherent narrative:
    - **Who the soul was** (Ketu sign/nakshatra + Karakamsha planets)
    - **What was mastered** (Ketu's house, D60 exaltations, strong 5th house)
    - **What was left unresolved** (12th house planets, retrograde planets, debilitated D60 planets)
    - **What debt is being paid** (Saturn's house/dignity, Kashta Phala, Mrita Avastha planets)
    - **What this life is for** (Rahu's direction, Atmakaraka's lesson, strong Ishta Phala planets)
    - **Remedies**: Sattvic practices to consciously resolve the key karmic debt — mantra for the AK planet, charity aligned with Saturn's afflictions, meditation aligned with Ketu's nakshatra deity.

## Output Structure

### 1. The Soul's Entry Point
Brief overview: Lagna, Atmakaraka, Ketu placement — what story does this soul arrive with?

### 2. The Past Life Narrative
A coherent, empathetic narrative of the most probable past life scenario — who they were, what they did, how they lived, what they failed to complete.

### 3. Karmic Debts & Wounds
Specific, honest identification of karmic debts (Saturn, Mrita planets, debilitated D60 planets, retrograde planets) and the life areas where these are manifesting as patterns of difficulty.

### 4. Gifts & Mastery Carried Forward
The talents, instincts, and natural abilities the soul has earned from past lives (Ketu house, D60 exalted planets, strong 5th house, Karakamsha planets).

### 5. The Soul's Assignment This Life
What Rahu, the Atmakaraka, and the Karakamsha demand as this life's evolutionary mission. Be specific.

### 6. Remedies for Karmic Resolution
- One mantra for the Atmakaraka planet
- One act of seva (selfless service) targeting Saturn's afflicted house
- One meditation / pilgrimages aligned with the Ketu nakshatra's deity
- Timing: when the current Dasha activates the key karmic nodes
