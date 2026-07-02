# Strict Workflow Router for Jyotish Readings

> **Purpose**: Prevent advanced techniques from being skipped. Route the user's plain-language question to a mandatory module checklist, then expose which modules were used, which were not used, and how omissions affect confidence.
>
> **Use this file before any Jyotish reading involving career timing, relationship timing, finance, event prediction, reliability verification, or advanced analysis.**

---

## 0. Core rule: do not let the user name the techniques

The user should not need to ask for Chara Dasha, A10, Argala, Shadbala, Ashtakavarga, KP, or divisional charts. Infer the question type and run the required checklist automatically.

Every non-trivial reading must end with a **Technique Audit Table**.

## 0.5 High-Rigor Override

When the user asks for maximum rigor, no guessing, past-event verification, raw evidence, or full parity with top open-source Jyotish engines, the reading enters **High-Rigor Override**.

Under this override, the engine must:

1. Attempt cross-reference against `PyJHora / VedAstro / jyotishganit`, while respecting license boundaries.
2. Use native repository implementations instead of lightweight summary scripts whenever a native module already exists.
3. Require `Vimshottari + Narayana Dasha` before making major timing claims; if they materially conflict, mark the conclusion `blocked` or downgrade confidence.
4. Force relevant divisional microscope layers:
   - `D10` + `A10` for career
   - `D2/D11` for wealth
   - `D9` + `UL` for relationship
5. Include raw outputs: exact degrees, dasha boundaries, Shadbala / AV values, Yoga names, ayanamsa / node mode, and external evidence pointers where available.

If any of the above cannot be completed because of missing birth precision, external oracle gaps, license quarantine, adapter failure, or missing field mapping, the report must explicitly say `blocked` rather than silently continuing with a fake-complete conclusion.

---

## 0.6 Existing MEVG Invocation Gate

This router reuses the existing MEVG source of truth in
`references/mandatory-verification-gate-protocol.md`; it does not create a
second verification system.

For **all chart interpretation readings**, including natal interpretation,
career, wealth, relationship, health, annual/monthly timing, event prediction,
rectification support, and technique reliability questions, the reading must
complete or explicitly block:

1. `MEVG / Global Web Evidence`: global web evidence collection, source tiering,
   and conflict arbitration.
2. `Real Case Calibration`: real case reference, benchmark case reference, or a
   clear case-gap statement with confidence downgrade.

The only exemption is: pure calculation / code / project-maintenance tasks are exempt
when they do not interpret chart meaning. Examples: running tests, checking Git
status, fixing code, or returning raw degrees / Dasha boundaries without any
fortune interpretation. Once the answer explains what the chart means, the
exemption no longer applies.

Every Level 2+ chart reading must include `MEVG / Global Web Evidence` and
`Real Case Calibration` in the Technique Audit Table.

---

## 0.7 User-Led Reading Calibration Gate

This gate turns the user's follow-up interrogation into workflow control. It is
not a personality preference; it prevents vague readings, memory-based
anchoring, and weak case analogies.

Trigger this gate when the user asks any of the following:

- whether a technique, source layer, oracle, or divisional chart was omitted;
- for a blind reading that excludes prior life events, feedback, or corrections;
- for concrete time/event options instead of conceptual questions;
- for real case comparison, global-web evidence, or a named analog case;
- why a timing claim was made, especially when a case dasha differs from the
  native's dasha.

When active, the reading must complete or explicitly block these controls:

1. `User Feedback Isolation`: if blind mode is requested, exclude prior
   biographical feedback, rectification choices, and user corrections from the
   interpretive reasoning. Use only birth inputs, current engine data, graded
   source packs, MEVG packets, and real-case calibration records.
2. `Concrete Time/Event Options`: for rectification, timing, opportunity, and
   event prediction, output selectable date windows and concrete event options.
   Do not ask vague subjective questions such as "does this feel like you?"
3. `Evidence-First / Conclusion-Last`: show raw chart layers, strength layers,
   dasha/transit/Tajika layers, MEVG, and real-case calibration before the final
   fortune judgment.
4. `Similarity-Weighted Case Calibration`: classify each real case by similarity
   layer instead of treating same-topic cases as equal evidence.
5. `Transferability Boundary`: state which part of an analog case transfers,
   which part does not, and how the mismatch changes confidence.
6. `Counterexample Handling`: mark counterexamples, user-excluded cases, and
   obsolete cases explicitly. Do not silently remove inconvenient cases.

### Similarity layers for real cases

| Layer | Meaning | Use |
|---|---|---|
| L0 same-domain only | Same broad topic, but no proven chart or dasha similarity | Background only |
| L1 D1 structure | Lagna, house lords, functional benefic/malefic roles, dignity, or house themes align | Weak support |
| L2 divisional support | Relevant D9/D10/D2/D4/D7/D12 etc. supports the same theme | Theme confidence |
| L3 functional dasha | Dasha periods play comparable functions even when the planets differ | Stage comparison |
| L4 verified event mechanism | Public biography or benchmark record shows a concrete event mechanism | Event-shape calibration |
| L5 material substrate | Income source, platform, institution, spouse/family support, or network structure is comparable | Required for material-outcome claims |

Analog cases cannot be used as prophecy. They may calibrate mechanism and
confidence only after the similarity layer and transferability boundary are
declared.

---

## 1. Question router

| User intent | Route | Required depth |
|---|---|---|
| "When will career opportunities appear?" / job / project / public status / profession | `career-timing-strict` | Level 3 |
| Marriage / partner / relationship timing | `relationship-timing-strict` | Level 3 |
| Money / income / gains / assets | `wealth-timing-strict` | Level 2 or 3 |
| "Will this event happen?" / concrete yes-no / project landing | `event-timing-strict` | Level 3 |
| "Why did this past event happen?" / technique reliability | `event-verification-strict` | Level 3 |
| General natal reading | `full-reading-strict` | Level 2 |
| PDF/文字星盘 | PDF quality gate first, then route by intent | Level 2 or 3 |

If the user asks for methodological rigor, academic validation, past-event verification, or "do not guess", upgrade to Level 3.

---

## 2. Shared mandatory baseline

For every Level 2+ reading, complete or explicitly mark unavailable:

- D1 Rashi: houses, lords, dignity, exact degrees, Nakshatra, dispositor chain.
- D9 Navamsa: dignity confirmation, Vargottama, major dignity reversals.
- Relevant divisional chart: D10 for career, D7 for children, D12 for family/ancestral themes, D2 for wealth, D24 for education.
- Vimshottari Dasha: MD/AD/PD when timing is requested.
- Transit: Saturn/Jupiter/Rahu-Ketu, plus Moon trigger for month/day-level timing.
- Functional benefic/malefic status by Lagna.
- Shadbala and Ashtakavarga when a claim depends on planetary strength or transit strength.
- MEVG external verification for all interpretive chart-reading claims.
- Real case calibration or a clearly marked case-evidence gap.
- Confidence label: A/B/C/insufficient.

---

## 3. `career-timing-strict`

Use when the user asks about career, profession, job, project, public recognition, work direction, script/project landing, status, or timing of new opportunity.

### Mandatory modules

| Layer | Required checks | Engine / reference |
|---|---|---|
| D1 career promise | 10H, 10L, 6H, 7H, 2H, 11H, Sun, Saturn, Mercury, Venus, exact degrees | `chart`, `aspects` |
| D9 confirmation | 10L dignity in D9, AK/AmK dignity, Vargottama | `varga-full`, `jaimini` |
| D10 execution | D10 Asc, 10H/10L, D10 Lagna lord, D10 Saturn/Sun/Mercury/Venus, D10 dispositor chain | `varga-full` |
| Dasha | Vimshottari MD/AD/PD; Dasha lord relation to 10H/10L/D10 | `dasha` |
| Jaimini | Chara Karaka, Amatya Karaka, Karakamsha, Chara Dasha | `jaimini --antardasha` |
| Arudha | AL and A10/Karma Pada if available | special lagna / manual if needed |
| Strength | Shadbala for Dasha lord, 10L, AmK, Saturn, Jupiter | `shadbala` |
| Transit strength | SAV/BAV for key transit signs and houses | `ashtakavarga` |
| Dispositor Chain | Final dispositor / energy flow for 10L, AmK, Saturn | `full-reading` |
| Inter-chart Linkage | D1->D9->D10 planet linkage for 10L, 2L, 11L | `full-reading` |
| Argala | Argala/Virodha on 10H, 10L, D10 10H, AmK | `argala` |
| KP / sub-lord | Use for yes/no or project landing questions | `nakshatra-adv`, KP references |
| Historical reliability | If user gives events, back-test same technique | `predict --past-verify` if applicable |

### Career timing output

Always separate:

1. **Opportunity contact**: message/interview/initial approach.
2. **Structural opportunity**: contract, formal role, long-term project, institution.
3. **Public/result manifestation**: release, payment, credit, visible status.

Do not merge these into one vague "career opportunity".

---

## 4. `relationship-timing-strict`

Use when the user asks marriage, relationship, spouse, partner, reconciliation, dating, or relationship outcome.

### Mandatory modules

- Confirm gender and day/night context before spouse significator analysis.
- D1: 7H, 7L, Venus, Jupiter, Mars, Moon, DK.
- D9: Lagna, 7H/7L, Venus/Jupiter, DK placement.
- Jaimini: Darakaraka, Upapada Lagna, Chara Dasha.
- Double Transit: Jupiter/Saturn activation of 7H/7L/DK/UL.
- Vimshottari: MD/AD/PD activation of 7H/7L/Venus/Jupiter/DK/UL.
- KP 7H sub-lord when asking if a relationship will formalize.
- Historical relationship event verification if available.

---

## 5. `wealth-timing-strict`

Use when the user asks money, income, payment, asset, gains, business profit, funding, debt, or financial recovery.

### Mandatory modules

- D1: 2H, 11H, 5H, 9H, 8H, 12H; 2L/11L; Jupiter, Venus, Mercury.
- D2 Hora if available; D10 if income is career-derived.
- Dasha: activation of 2L/11L/5L/9L/10L and D2/D10 indicators.
- Shadbala: 2L/11L/Jupiter/Venus/Mercury.
- Ashtakavarga: SAV/BAV of 2H/11H and transit Jupiter/Saturn positions.
- Argala: opening/blocking on 2H and 11H.
- KP: use for payment到账/settlement yes-no questions.

---

## 6. `event-timing-strict`

Use when the user asks for concrete timing, yes/no, project approval, launch, move, travel, contract, payment, or whether something will happen.

### Mandatory modules

1. Define the event house and event significators.
2. Check natal promise in D1 and relevant Varga.
3. Check Vimshottari MD/AD/PD.
4. Cross-check Jaimini static indicators if event is major; Chara Dasha timing is partial and must be treated as low-weight corroboration only.
5. Check Saturn/Jupiter/Rahu-Ketu transit to event houses/lords.
6. Check Double Transit where applicable.
7. Use KP/Sub-lord if the question is binary or landing-specific.
8. Use Moon transit only as a trigger inside an already-supported window.
9. Give time windows, not unsupported exact-day claims.

---

## 7. `event-verification-strict`

Use when the user provides past events and asks whether the technique is reliable.

### Method

1. Extract the exact event date or window.
2. Identify which prediction rule would have implied it.
3. Apply the same rule to the past event without changing interpretation after seeing the result.
3.5. Check Dispositor Chain and Inter-chart Linkage for consistency across D1/D9/D10.
4. Score match quality:
   - A: same theme + same timing + multiple systems support.
   - B: same theme + approximate timing or delayed manifestation.
   - C: symbolic match only.
   - Fail: contradicted by event.
5. Convert the result into a personalized rule only after at least two matching examples.

### Output table

| Past event | Technique tested | Match | Adjustment |
|---|---|---|---|
| date/window + event | rule | A/B/C/fail | keep/downgrade/modify |

---

## 8. Technique Audit Table

Every Level 2+ output must include this table near the end.

| Technique | Status | Key result | Effect on confidence |
|---|---|---|---|
| D1 | Used / not used | ... | ... |
| D9 | Used / not used | ... | ... |
| D10 / relevant Varga | Used / not used | ... | ... |
| Functional Benefic/Malefic | Used / not used / blocked | Key functional benefics, malefics, functional neutrals, yogakarakas | Mandatory in high-rigor mode; lower confidence or mark blocked if omitted |
| Vimshottari | Used / not used | ... | ... |
| Jaimini / Chara Dasha | Used / partial / not used | Karaka/Karakamsha reliable; Chara Dasha timing partial if used | Cap timing confidence unless independently corroborated |
| AmK / Karakamsha | Used / not used | ... | ... |
| AL / A10 | Used / partial / unavailable | ... | ... |
| Shadbala | Used / partial / not used | Internally consistent relative strength; external absolute calibration pending | Cap precise strength claims |
| Ashtakavarga | Used / not used | ... | ... |
| Dispositor Chain | Used / not used | ... | ... |
| Inter-chart Linkage | Used / not used | ... | ... |
| Tajika Yogas | Used / partial / not used | Ithasala/Easarapha/Nakta etc. | Cap annual timing confidence |
| Sahams | Used / partial / not used | Punya/Karya/Vivah etc. | Cap event timing confidence |
| Darakaraka (DK) | Used / not used | Marriage/partner analysis | Cap marriage timing without DK |
| Raj Yoga | Used / partial / not used | Power/status yogas | Cap high-status event confidence |
| Dhana Yoga | Used / partial / not used | Wealth/money yogas | Cap wealth timing confidence |
| Pancha Mahapurusha | Used / partial / not used | 5 Mahapurusha yogas | Cap personality strength assessment |
| Neecha Bhanga Raj | Used / partial / not used | Debilitation recovery | Cap comeback/recovery timing |
| Mangal Dosha | Used / not used | Mars in bad houses | Cap marriage difficulty assessment |
| Kaal Sarp Dosha | Used / not used | All planets Rahu-Ketu side | Cap obstacle analysis |
| Pitra Dosha | Used / not used | Sun-Rahu or Sun afflicted | Cap ancestor karma analysis |
| Sade Sati | Used / partial / not used | Saturn 7.5-year period | Cap Saturn pressure timing |
| Arudha Lagna (AL) | Used / not used | Mirror Lagna (perception) | Cap public image analysis |
| Upapada Lagna (UL) | Used / not used | Marriage partner indicator | Cap marriage quality analysis |
| Argala | Used / not used | ... | ... |
| KP / Sub-lord | Used / not required / unavailable | ... | ... |
| Historical verification | Used / not provided | ... | ... |
| User Feedback Isolation | Used / not requested / blocked | Blind-mode exclusion of prior biography, rectification feedback, and user corrections | Required when user asks for blind reading; blocked if isolation cannot be guaranteed |
| Concrete Time/Event Options | Used / not required / blocked | Date windows with selectable concrete event options | Required for rectification and timing calibration; lowers precision if omitted |
| Similarity-Weighted Case Calibration | Used / blocked / case gap | L0-L5 similarity layer for each analog case | Same-topic cases alone cannot raise confidence |
| Transferability Boundary | Used / blocked / not applicable | What transfers, what does not, and why | Prevents copying a celebrity or benchmark story into the native's forecast |
| MEVG / Global Web Evidence | Used / blocked / exempt for pure calculation | Source tier, searches, conflict arbitration | Mandatory for all chart interpretation readings; blocked or downgraded if omitted |
| Real Case Calibration | Used / blocked / case gap | Real case, benchmark case, or documented lack of matching cases | Cap confidence when no comparable case evidence is available |

Never omit unavailable techniques silently. Mark them as unavailable or not integrated.
When Functional Benefic/Malefic is used, explicitly surface the functional neutrals and yogakarakas instead of collapsing them into a generic summary.

---

## 9. Known product gaps

The current skill has strong coverage. Do not describe a technique as simply “missing”; classify it by capability layer. See `references/technique-capability-matrix.md` and the machine-readable `references/technique_registry.json`. For automated checks, run `python scripts/jyotish_engine.py audit-capabilities --mode validate` or `--mode table --route <route_id>`.

| Gap / partial area | Current handling | Impact |
|---|---|---|
| A10 / 10th Arudha / Karma Pada | Covered from v6.0.2 via `full-reading.modules.special_lagnas.A10_Karma_Pada` | If `full-reading` is not run, mark not called rather than missing |
| Full Bhava Chalit | Use cusp/KP data if present; otherwise mark partial | House placement near cusps may need recalibration |
| Pushkara Navamsa / Pushkara Bhaga automation | Covered from v6.0.2 via `full-reading.modules.pushkara` for D1 planet flags | If exact degrees are absent, mark manual/unavailable |
| Vargottama | Covered from v6.0.2 via `full-reading.modules.vargottama` | If D9 is absent, mark unavailable |
| Sudarshana Chakra | D1×D9×D10 triangle verification exists as partial substitute | Traditional Sudarshana module still absent |
| Dasha Sandhi | Covered from v6.0.2 via `full-reading.modules.dasha_sandhi` | Only detects MD/AD boundaries within the configured orb |
| Strict output orchestration | This file provides the workflow | Must be followed explicitly |

---

## 10. Confidence rules

| Confidence | Requirements |
|---|---|
| A | Natal promise + relevant Varga + Dasha + Transit + at least one verification layer support. For personal prediction, historical back-test preferred. |
| B | Three major systems support, but one key layer missing or timing is broad. |
| C | One or two indicators only; symbolic or exploratory. |
| Insufficient | Missing birth data, missing relevant Varga, no Dasha support, or unsupported exact timing. |

Do not upgrade confidence because the interpretation sounds elegant. Upgrade only when independent techniques converge.

---

## 11. Output discipline

- State what the question type is.
- State which strict route was used.
- Separate promise, activation, trigger, and manifestation.
- Separate contact, formalization, and visible result.
- Flag missing modules explicitly.
- Avoid industry-specific guessing unless the chart and user-provided context both support it.
- If the user asks for academic rigor, include technique limitations and failure modes.
