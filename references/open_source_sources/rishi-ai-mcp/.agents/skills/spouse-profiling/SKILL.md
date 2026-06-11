---
name: spouse-profiling
description: "Use when the user wants to know what their future spouse looks like, their personality, archetype, traits, career, lifestyle, or any detailed profile of the spouse based on the native's chart."
---

# Spouse Profiling Workflow

TRIGGER: Use this skill when the user asks what their spouse will be like, what they look like, what kind of person they'll marry, what the spouse's personality or archetype is, or how to recognize their future partner.

> **Note:** This skill does NOT require the spouse's birth details. Everything is derived entirely from the **native's own chart** using the classical Jyotish indicators of the 7th house, Darakaraka, Upapada, Venus/Jupiter, and their Navamsha positions.

---

## Steps

1. **Fetch Chart Data**: Call `cast_vedic_chart` (birth parameters only). Transit data is not required for spouse profiling.

2. **Identify the Native's Gender** — Ask if not already known. This determines:
   - **Male chart**: Venus = natural significator of the wife. Analyze Venus primarily.
   - **Female chart**: Jupiter = natural significator of the husband. Analyze Jupiter primarily.

3. **Darakaraka (The Spouse Soul-Planet)**:
   - From `jaimini_karakas`, read the **Darakaraka** — the planet with the lowest degree in the chart. This is the single most important indicator of the spouse's inner nature and soul-level identity.
   - Read its `sign`, `house`, `dignity`, `nakshatra`, `nakshatra_lord`, `is_retrograde`, `shadbala.percentage`, and `avasthas`.
   - Read its `d9_sign` — the Darakaraka in Navamsha reveals the real, deep nature of the spouse as the relationship matures.
   - Each Darakaraka planet produces a distinct spouse archetype:
     - **Sun DK**: Authoritative, proud, leader-type, government/corporate lineage. Bright complexion. Strong opinions. Seeks admiration.
     - **Moon DK**: Nurturing, emotionally sensitive, intuitive, artistic or caring profession. Soft features, expressive eyes. Moody but deeply empathetic.
     - **Mars DK**: Athletic, assertive, driven, bold. Strong physical build. Entrepreneurial or in physically demanding fields. Passionate and direct.
     - **Mercury DK**: Intellectual, witty, communicative, youthful-looking. May be in tech, writing, commerce, or education. Quick-minded, curious, adaptable.
     - **Jupiter DK**: Wise, principled, generous, teacher or advisor archetype. Well-built, warm presence. Strong ethics. Comes from a respectable family.
     - **Venus DK**: Artistic, beautiful/handsome, charming, refined taste. Creative field or luxury sector. Deeply romantic.
     - **Saturn DK**: Older appearance than age, serious, disciplined, hardworking. May be in law, administration, or manual expertise. Slow to open emotionally but extremely loyal once committed.
     - **Rahu DK**: Unconventional, foreign connection possible, ambitious, modern, may have an unusual background or multicultural identity.
     - **Ketu DK**: Spiritually inclined, introverted, emotionally complex, may seem detached or mysterious. Past-life connection is very likely.

4. **7th House (The Partner's Outer Form)**:
   - Determine the 7th house sign from the Lagna sign (7 signs away whole-sign).
   - The **7th house sign** reveals the spouse's physical form, temperament, and the native's projected desire for a partner:
     - **Aries 7th**: Energetic, athletic, sharp facial features, competitive, initiates things. Often first-born.
     - **Taurus 7th**: Beautiful, well-built body, sensual, fond of comfort and nature, stable temperament.
     - **Gemini 7th**: Slim, communicative, intelligent, youthful, may have dual nature or occupations.
     - **Cancer 7th**: Round face, nurturing, emotional, family-oriented, may work in caregiving or home-related fields.
     - **Leo 7th**: Regal, well-groomed, leadership presence, generous, proud, bright appearance.
     - **Virgo 7th**: Slim, analytical, perfectionistic, health-conscious, detail-oriented, clean habits.
     - **Libra 7th**: Very attractive, balanced features, diplomatic, artistic, socially skilled.
     - **Scorpio 7th**: Intense, magnetic, piercing eyes, emotionally deep, may have secretive tendencies.
     - **Sagittarius 7th**: Tall, philosophical, free-spirited, may be from a different culture or religion.
     - **Capricorn 7th**: Structured, responsible, mature, may be older or more serious. Strong jaw/bone structure.
     - **Aquarius 7th**: Unconventional, intellectual, progressive, may have a unique or eccentric lifestyle.
     - **Pisces 7th**: Dreamy, soft features, artistic or spiritual, compassionate, may work in healing or creative arts.

5. **7th Lord (The Spouse's Manifest Personality)**:
   - Identify the lord of the 7th house sign. Read its `sign`, `house`, `nakshatra`, `dignity`, `shadbala.percentage`, `avasthas`, and `d9_sign`.
   - The 7th lord's **nakshatra** gives the texture of the spouse's most dominant trait personality — read the nakshatra's classical nature and apply it to the spouse description.
   - The 7th lord's **house placement** reveals the domain of life through which the spouse and marriage manifest:
     - 1st: Spouse is very similar to native, may be a close acquaintance.
     - 2nd: Spouse from a wealthy/well-spoken family; relationship connected to money.
     - 3rd: Known through siblings, media, short travel, or communication field.
     - 4th: Local connection, homebody tendency, may be from native's hometown area.
     - 5th: Love marriage or creative field connection. Romantic and playful partner.
     - 6th: May meet through work, service, or health sector. Can bring conflicts.
     - 7th: Very partner-focused spouse; may be in partnerships/business.
     - 8th: Intense, transformative connection; may have hidden or complex background.
     - 9th: Foreign or philosophical connection; highly principled or from different belief system.
     - 10th: Career-driven, ambitious spouse; met through professional circles.
     - 11th: Friend-turned-lover; social circle or network connection.
     - 12th: Foreign / distant / private spouse; or met through spiritual/hospital/travel context.
   - The 7th lord's **dignity** determines the quality of the spouse's character and refinement: exalted = exceptional, debilitated = complex or struggling in some domain.

6. **Venus / Jupiter (Natural Significator of the Spouse)**:
   - For males: **Venus** sign, nakshatra, house, dignity, `d9_sign`. Venus in D9 is particularly revealing — this shows what the wife actually becomes in the marriage.
   - For females: **Jupiter** sign, nakshatra, house, dignity, `d9_sign`. Jupiter in D9 reveals the actual husband.
   - The **nakshatra of Venus/Jupiter** gives the dominant emotional and aesthetic archetype the native is fated to attract.
   - Important Nakshatras and their spouse archetypes:
     - Rohini: highly sensual, beautiful, attached to material comfort.
     - Magha: royal bearing, lineage pride, authoritative.
     - Purva Phalguni: creative, pleasure-loving, charming, romantic.
     - Hasta: practical, skilled with hands, intelligent, organized.
     - Chitra: aesthetically beautiful, artistic, glamorous.
     - Swati: independent, flexible, business-minded.
     - Vishakha: goal-driven, passionate, dual-natured.
     - Anuradha: deeply loyal, emotionally rich, spiritual bond.
     - Jyeshtha: protective, intense, leadership capacity.
     - Purva Ashadha: idealistic, creative, strong opinions.
     - Uttara Ashadha: ethical, responsible, quiet strength.
     - Shravana: attentive listener, traditional values, wise.
     - Dhanishtha: ambitious, musical/rhythmic, strong-willed.
     - Purva Bhadrapada: passionate, idealistic, intense internal world.
     - Revati: compassionate, nurturing, otherworldly gentleness.

7. **Upapada Lagna (UL) — The Spouse's Social Identity**:
   - From `upapada`, read the UL sign and its lord (`lord` field).
   - The **UL sign** indicates the social and worldly archetype of the spouse — how they appear to society, their class bearing and social identity.
   - The **UL lord's placement** (house in D1) indicates what domain of life the UL lord operates in — this further specifies the spouse's life context and background.
   - If the **UL lord is exalted** or in own sign: spouse comes from a distinguished, high-status family or background.
   - If the **UL lord is debilitated** or afflicted: spouse may come from a troubled background or face personal hardships.

8. **Dara Pada (A7) — The Spouse's Public Image**:
   - From `arudha_padas`, read A7 (`arudha_padas["7"]`).
   - The A7 sign indicates how the spouse will be *seen by the world* — their social presence, public archetype, and magnetic appeal.
   - Planets in or aspecting A7 modify the spouse's public persona.

9. **Navamsha (D9) — The Spouse's Inner Reality**:
   - The **7th house in D9** (count 7 from the `lagna.d9_sign`) reveals the inner nature of the spouse that only the native gets to see behind closed doors.
   - The **Darakaraka's D9 sign** is the most revealing layer — who the spouse truly is at the soul level.
   - Vargottama status of Venus/Jupiter (if `d9_sign` = D1 `sign`): extremely strong spouse indicator — the spouse's nature described by Venus/Jupiter is exceptionally strong and dependable.

10. **Physical Appearance Synthesis**:
    Use the 7th house sign, Darakaraka sign, and Venus/Jupiter sign collectively to construct the physical description. Synthesize as follows:
    - **Body type**: Derived from element of 7th house sign (Fire = athletic/lean/sharp, Earth = solid/well-built/sensual, Air = slim/tall/expressive, Water = soft/rounded/emotional).
    - **Facial features**: Darakaraka sign's classical body part rulership and sign archetype.
    - **Complexion**: Sun-influenced signs (Leo, Aries) = bright/fair; Moon signs (Cancer) = pale/soft; Saturn signs (Capricorn, Aquarius) = dark/dusky; Venus signs (Taurus, Libra) = glowing/attractive.
    - **Hair and eyes**: Nakshatra of the Darakaraka / Venus — each nakshatra has classical hair/eye descriptions.
    - **Age relative to native**: Saturn influence on 7th = older; Jupiter = similar age or slightly older; mars = similar or younger; Rahu = unpredictable age difference.

11. **Personality & Emotional Style**:
    Synthesize from:
    - Darakaraka planet's natural planetary nature (Sun = ego-driven, Moon = emotional, Mars = assertive, Mercury = intellectual, Jupiter = wise, Venus = aesthetic, Saturn = serious, Rahu = ambitious/unusual, Ketu = spiritual/detached)
    - 7th house sign's elemental and modal quality (Cardinal = initiator, Fixed = steadfast, Mutable = adaptable)
    - 7th lord nakshatra's dominant trait
    Deliver a clear character sketch: introvert/extrovert, communication style, love language, emotional needs, core values.

12. **Career & Lifestyle of Spouse**:
    - **Darakaraka planet's natural domain**: Sun = government/politics/medicine; Moon = hospitality/food/care; Mars = engineering/military/sports; Mercury = tech/writing/commerce; Jupiter = law/teaching/finance; Venus = arts/fashion/beauty/luxury; Saturn = agriculture/labor/law/administration.
    - **7th lord's house placement**: Confirms life domain where spouse operates.
    - **UL lord's house placement**: Gives the social and professional context of the spouse's background.

13. **Where & How You'll Meet**:
    - 7th lord's house placement (step 5) gives the primary meeting context.
    - 11th house and its lord: social networks and friend groups involved.
    - Rahu: if connected to 7th or DK, may involve online/digital/unconventional meeting.
    - Darakaraka in a movable sign (Aries, Cancer, Libra, Capricorn): chance encounter while traveling or on the move.
    - Darakaraka in a fixed sign (Taurus, Leo, Scorpio, Aquarius): stable, known environments — work, family, social circles.
    - Darakaraka in a dual sign (Gemini, Virgo, Sagittarius, Pisces): educational, communicative, or philosophical settings.

14. **Compatibility Archetype (Attraction Chemistry)**:
    - The Yoni of the native's Moon nakshatra vs. the predicted Yoni of the spouse's Moon nakshatra (based on DK's nakshatra) reveals physical compatibility archetype.
    - Gana: if the native's Moon nakshatra Gana (Deva/Manushya/Rakshasa) aligns with DK indicators, the couple's temperamental match is strong.

15. **Synthesize — The Spouse Profile**:
    Deliver the final output in a structured, vivid, and actionable format:

    ### Physical Blueprint
    Detailed description of probable looks: height, build, complexion, face shape, hair, eyes.

    ### Personality Archetype
    A named archetype (e.g., "The Quiet Intellectual," "The Regal Leader," "The Free-Spirited Artist") + 4-5 core personality traits.

    ### Emotional & Relational Style
    How the spouse loves, communicates, handles conflict, and what they need emotionally from the native.

    ### Career & Social Background
    Probable professional domain, family/social class indicators, educational type.

    ### How & Where to Find Them
    The specific settings, contexts, and timing windows where this person is most likely to be encountered.

    ### Recognition Signals
    3-5 very specific traits the native should look out for — the "green flags" that signal this is the one their chart describes.
